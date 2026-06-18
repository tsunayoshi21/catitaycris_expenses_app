import imaplib
import email
import email.utils
from email.header import decode_header
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone as dj_timezone
from asgiref.sync import sync_to_async
import unicodedata

from apps.accounts.models import Account, SystemState
from apps.transactions.models import Transaction, TelegramNotification, Category
from apps.users.models import CustomUser
from .llm import parse_email as llm_parse_email, LLMServiceError, categorize
from .payment_parser import parse_national_payment, parse_international_payment
from .reconciliation import reconcile_national_payment, reconcile_international_payment
from .fx import fetch_usd_clp

logger = logging.getLogger(__name__)

SUBJECT_KIND = {
    'transferencia a terceros': 'transferencia',
    'cargo en cuenta': 'debito',
    'compra con tarjeta de credito': 'compra',
    'pago de tarjeta de credito nacional': 'pago_nacional',
    'pago de tarjeta de credito internacional': 'pago_internacional',
}


def _normalize_subject(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def classify_subject(subject):
    return SUBJECT_KIND.get(_normalize_subject(subject))


def build_purchase_fields(parsed: dict, fallback_rate) -> dict:
    monto = Decimal(str(parsed.get('monto', 0)))
    moneda = parsed.get('moneda', 'CLP')
    if moneda == 'USD':
        amount_clp = (monto * fallback_rate).quantize(Decimal('0.01')) if fallback_rate else None
        return {'currency': 'USD', 'amount_clp': amount_clp, 'fx_status': 'estimated'}
    return {'currency': 'CLP', 'amount_clp': monto, 'fx_status': 'na'}


class EmailProcessor:
    def __init__(self, account):
        self.account = account
        self.imap_user, self.imap_password = account.get_imap_credentials()

    def _decode_header(self, val):
        if not val:
            return ''
        parts = decode_header(val)
        out = []
        for txt, enc in parts:
            if isinstance(txt, bytes):
                try:
                    out.append(txt.decode(enc or 'utf-8', errors='ignore'))
                except Exception:
                    out.append(txt.decode('utf-8', errors='ignore'))
            else:
                out.append(txt)
        return ''.join(out)

    def extract_text_from_email(self, msg):
        text_content = None
        html_content = None
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get('Content-Disposition'))
                if ct == 'text/plain' and 'attachment' not in cd:
                    text_content = part.get_payload(decode=True).decode(
                        part.get_content_charset() or 'utf-8', errors='ignore'
                    )
                elif ct == 'text/html' and 'attachment' not in cd:
                    html_content = part.get_payload(decode=True).decode(
                        part.get_content_charset() or 'utf-8', errors='ignore'
                    )
        else:
            if msg.get_content_type() == 'text/plain':
                text_content = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or 'utf-8', errors='ignore'
                )
            elif msg.get_content_type() == 'text/html':
                html_content = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or 'utf-8', errors='ignore'
                )
        if not text_content and html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator='\n', strip=True)
        return text_content

    def _build_imap_search(self):
        search_parts = []
        cutoff = self._ensure_utc(self.account.last_checked)
        if cutoff:
            date_str = cutoff.strftime('%d-%b-%Y')
            search_parts.extend(['SINCE', date_str])
        allowed_senders = [s for s in settings.BANK_SENDERS if s]
        if allowed_senders:
            from_parts = []
            for sender in allowed_senders:
                from_parts.extend(['FROM', sender])
            if len(allowed_senders) > 1:
                or_parts = ['OR']
                or_parts.extend(from_parts)
                search_parts = or_parts + search_parts if search_parts else or_parts
            else:
                search_parts = from_parts + search_parts
        return '(' + ' '.join(search_parts) + ')' if search_parts else '(UNSEEN)'

    def _parse_email_date(self, msg):
        date_hdr = msg.get('Date')
        if not date_hdr:
            return None
        try:
            return self._ensure_utc(email.utils.parsedate_to_datetime(date_hdr))
        except Exception:
            return None

    def _ensure_utc(self, dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _is_from_bank(self, email_from):
        from_lower = email_from.lower()
        return any(sender in from_lower for sender in settings.BANK_SENDERS)

    def _create_email_data(self, msg, parsed_data, kind, current_rate=None):
        msg_dt = self._parse_email_date(msg)
        msg_id = msg.get('Message-ID') or f'{self.account.id}:{id(msg)}'
        date_val = msg_dt or datetime.now(timezone.utc)
        if parsed_data.get('fecha_iso'):
            try:
                date_val = self._ensure_utc(datetime.fromisoformat(parsed_data['fecha_iso']))
            except Exception:
                pass
        data = {
            'kind': kind,
            'email_id': msg_id,
            'date': date_val,
            'amount': parsed_data.get('monto', 0.0),
            'merchant': parsed_data.get('comercio'),
            'type': parsed_data.get('tipo_transaccion', 'desconocido'),
            'email_date': msg_dt,
        }
        # Purchases carry multi-currency fields derived from the parsed currency
        if kind == 'compra':
            data.update(build_purchase_fields(parsed_data, current_rate))
        return data

    def _create_payment_data(self, msg, body, kind):
        msg_dt = self._parse_email_date(msg)
        msg_id = msg.get('Message-ID') or f'{self.account.id}:{id(msg)}'
        date_val = msg_dt or datetime.now(timezone.utc)
        data = {
            'kind': kind,
            'email_id': msg_id,
            'date': date_val,
            'merchant': None,
            'type': 'pago_tarjeta',
            'currency': 'CLP',
            'fx_status': 'na',
            'email_date': msg_dt,
        }
        if kind == 'pago_nacional':
            monto = parse_national_payment(body)
            data['amount'] = monto
            data['amount_clp'] = monto
        else:  # pago_internacional
            usd_paid, clp_total = parse_international_payment(body)
            data['amount'] = clp_total
            data['amount_clp'] = clp_total
            data['usd_paid'] = usd_paid
            data['clp_total'] = clp_total
        return data

    async def process_emails(self, current_rate=None):
        logger.info('Conectando a IMAP %s para cuenta %s', self.account.imap_host, self.account.id)
        conn = imaplib.IMAP4_SSL(self.account.imap_host, settings.IMAP_PORT)
        new_transactions = []
        max_date_seen = self._ensure_utc(self.account.last_checked)
        try:
            conn.login(self.imap_user, self.imap_password)
            logger.info('Login IMAP exitoso para cuenta %s', self.account.id)
            conn.select(settings.IMAP_FOLDER)
            criteria = self._build_imap_search()
            status, data = conn.search(None, criteria)
            if status != 'OK':
                logger.warning('IMAP search fallo para cuenta %s: status=%s', self.account.id, status)
                return []
            email_ids = data[0].split()
            logger.info(
                'Encontrados %d emails para cuenta %s (criterio: %s)',
                len(email_ids), self.account.id, criteria,
            )
            for eid in email_ids:
                try:
                    email_data = await self._process_single_email(conn, eid, current_rate)
                    if email_data:
                        new_transactions.append(email_data)
                        if email_data['email_date']:
                            if max_date_seen is None or email_data['email_date'] > max_date_seen:
                                max_date_seen = email_data['email_date']
                except Exception as e:
                    logger.error('Error procesando email %s: %s', eid, e)
            if max_date_seen:
                await sync_to_async(self._update_last_checked)(max_date_seen)
            logger.info(
                'Procesamiento completo para cuenta %s: %d transacciones nuevas',
                self.account.id, len(new_transactions),
            )
            return new_transactions
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def _update_last_checked(self, new_date):
        account = Account.objects.get(pk=self.account.pk)
        utc_date = self._ensure_utc(new_date)
        last_utc = self._ensure_utc(account.last_checked)
        if utc_date and (last_utc is None or utc_date > last_utc):
            account.last_checked = utc_date
            account.save(update_fields=['last_checked'])

    async def _process_single_email(self, conn, email_id, current_rate=None):
        status, msg_data = conn.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None
        raw_msg = msg_data[0][1]
        msg = email.message_from_bytes(raw_msg)
        from_header = self._decode_header(msg.get('From', ''))
        if not self._is_from_bank(from_header):
            logger.debug('Email %s descartado: remitente no bancario (%s)', email_id, from_header[:50])
            return None
        msg_id = msg.get('Message-ID') or f'{self.account.id}:{email_id.decode()}'
        is_duplicate = await sync_to_async(
            lambda: Transaction.objects.filter(raw_email_id=msg_id).exists()
        )()
        if is_duplicate:
            logger.debug('Email duplicado: %s', msg_id)
            return None
        subject = self._decode_header(msg.get('Subject', ''))
        body = self.extract_text_from_email(msg)
        kind = classify_subject(subject)
        if kind is None:
            logger.debug('Email %s descartado: asunto no soportado (%s)', email_id, subject[:50])
            return None
        if kind in ('compra', 'debito', 'transferencia'):
            try:
                parsed_data = await llm_parse_email(subject, body)
            except LLMServiceError as e:
                await sync_to_async(_pause_polling_on_llm_error)(str(e))
                raise
            return self._create_email_data(msg, parsed_data, kind, current_rate)
        # pagos: pago_nacional / pago_internacional
        return self._create_payment_data(msg, body, kind)


def _pause_polling_on_llm_error(reason: str):
    state = SystemState.get()
    state.polling_paused = True
    state.paused_reason = reason
    state.paused_at = dj_timezone.now()
    state.admin_notified = False
    state.save(update_fields=['polling_paused', 'paused_reason', 'paused_at', 'admin_notified'])
    logger.error('Polling pausado por error LLM: %s', reason)


async def poll_once():
    logger.info('Iniciando ciclo de polling')

    state = await sync_to_async(SystemState.get)()
    if state.polling_paused:
        logger.info('Polling pausado. Esperando reanudacion admin.')
        return []

    accounts = await sync_to_async(
        lambda: list(
            Account.objects.filter(
                enabled=True,
                users__telegram_chat_id__isnull=False,
            ).distinct()
        )
    )()
    if not accounts:
        logger.warning('No hay cuentas habilitadas con usuarios vinculados a Telegram')
        return []

    # Tasa USD/CLP best-effort una vez por ciclo; None si falla (compras USD quedan sin amount_clp).
    try:
        current_rate = await sync_to_async(fetch_usd_clp)()
    except Exception as e:
        logger.warning('No se pudo obtener tasa USD/CLP: %s', e)
        current_rate = None

    all_new = []
    for account in accounts:
        try:
            processor = EmailProcessor(account)
            new_emails = await processor.process_emails(current_rate)
            for email_data in new_emails:
                user = await sync_to_async(
                    lambda a=account: a.users.filter(telegram_chat_id__isnull=False).first()
                )()
                if not user:
                    logger.warning('Cuenta %s sin usuarios', account.id)
                    continue

                def _create_tx(u=user, ed=email_data):
                    return Transaction.objects.create(
                        user=u,
                        date=ed['date'],
                        amount=ed['amount'],
                        merchant=ed['merchant'],
                        type=ed['type'],
                        raw_email_id=ed['email_id'],
                        currency=ed.get('currency', 'CLP'),
                        amount_clp=ed.get('amount_clp'),
                        fx_status=ed.get('fx_status', 'na'),
                    )

                tx = await sync_to_async(_create_tx)()
                all_new.append(tx)

                # Pagos de tarjeta disparan reconciliacion contra compras pendientes.
                if email_data.get('kind') == 'pago_nacional':
                    try:
                        await sync_to_async(reconcile_national_payment)(tx)
                        logger.info('Reconciliacion nacional ejecutada para pago tx #%s', tx.id)
                    except Exception as e:
                        logger.warning('Reconciliacion nacional fallo para pago tx #%s: %s', tx.id, e)
                elif email_data.get('kind') == 'pago_internacional':
                    try:
                        await sync_to_async(reconcile_international_payment)(
                            tx, email_data['usd_paid'], email_data['clp_total']
                        )
                        logger.info('Reconciliacion internacional ejecutada para pago tx #%s', tx.id)
                    except Exception as e:
                        logger.warning('Reconciliacion internacional fallo para pago tx #%s: %s', tx.id, e)

                # Best-effort categorization using merchant info
                if tx.merchant:
                    try:
                        valid_cats = await sync_to_async(
                            lambda: list(Category.get_valid_for_user(user.id).values_list('name', flat=True))
                        )()
                        cat_name = await categorize(tx.merchant, tx.merchant, user_id=user.id, valid_categories=valid_cats)

                        def _set_category(t=tx, cn=cat_name, uid=user.id):
                            cat_obj = Category.get_valid_for_user(uid).filter(name=cn).first()
                            t.category_name = cn
                            t.category = cat_obj
                            t.save(update_fields=['category_name', 'category', 'updated_at'])

                        await sync_to_async(_set_category)()
                        logger.info('Categoria auto-asignada para tx #%s: %s', tx.id, cat_name)
                    except Exception as e:
                        logger.warning('Auto-categorizacion fallo para tx #%s: %s', tx.id, e)

                if email_data.get('type') != 'pago_tarjeta':
                    def _create_notif(u=user, t=tx):
                        return TelegramNotification.objects.create(user=u, transaction=t)

                    await sync_to_async(_create_notif)()
                logger.info('Nueva transaccion creada: tx_id=%s', tx.id)
        except Exception as e:
            logger.exception('Error procesando cuenta %s: %s', account.id, e)

    logger.info('Ciclo de polling completo: %d transacciones nuevas en total', len(all_new))
    return all_new


async def run_poller():
    logger.info('Iniciando email poller (intervalo %ss)', settings.POLL_INTERVAL)
    while True:
        try:
            new_txs = await poll_once()
            if new_txs:
                logger.info('Total nuevas transacciones: %d', len(new_txs))
            await asyncio.sleep(settings.POLL_INTERVAL)
        except Exception as e:
            logger.exception('Error en poller: %s', e)
            await asyncio.sleep(settings.POLL_INTERVAL)
