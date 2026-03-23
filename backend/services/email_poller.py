import imaplib
import email
import email.utils
from email.header import decode_header
import time
import re
import asyncio
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)


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

    def is_subject_supported(self, subject):
        valid_subjects = [
            'Transferencia a Terceros',
            'Cargo en Cuenta',
            'Compra con Tarjeta de Credito',
        ]
        return subject in valid_subjects

    def _create_email_data(self, msg, parsed_data):
        msg_dt = self._parse_email_date(msg)
        msg_id = msg.get('Message-ID') or f'{self.account.id}:{id(msg)}'
        date_val = msg_dt or datetime.now(timezone.utc)
        if parsed_data.get('fecha_iso'):
            try:
                date_val = self._ensure_utc(datetime.fromisoformat(parsed_data['fecha_iso']))
            except Exception:
                pass
        return {
            'email_id': msg_id,
            'date': date_val,
            'amount': parsed_data.get('monto', 0.0),
            'merchant': parsed_data.get('comercio'),
            'type': parsed_data.get('tipo_transaccion', 'desconocido'),
            'suggested_category': parsed_data.get('posible_categoria', 'sin categoria'),
            'email_date': msg_dt,
        }

    def process_emails(self):
        from .llm import parse_email as llm_parse_email
        logger.debug('Procesando cuenta %s (last_checked=%s)', self.account.id, self.account.last_checked)
        conn = imaplib.IMAP4_SSL(self.account.imap_host, settings.IMAP_PORT)
        new_transactions = []
        max_date_seen = self._ensure_utc(self.account.last_checked)
        try:
            conn.login(self.imap_user, self.imap_password)
            conn.select(settings.IMAP_FOLDER)
            criteria = self._build_imap_search()
            status, data = conn.search(None, criteria)
            if status != 'OK':
                return []
            email_ids = data[0].split()
            logger.debug('Encontrados %d emails', len(email_ids))
            for eid in email_ids:
                try:
                    email_data = self._process_single_email(conn, eid, llm_parse_email)
                    if email_data:
                        new_transactions.append(email_data)
                        if email_data['email_date']:
                            if max_date_seen is None or email_data['email_date'] > max_date_seen:
                                max_date_seen = email_data['email_date']
                except Exception as e:
                    logger.error('Error procesando email %s: %s', eid, e)
            if max_date_seen:
                self._update_last_checked(max_date_seen)
            return new_transactions
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def _update_last_checked(self, new_date):
        from apps.accounts.models import Account
        account = Account.objects.get(pk=self.account.pk)
        utc_date = self._ensure_utc(new_date)
        last_utc = self._ensure_utc(account.last_checked)
        if utc_date and (last_utc is None or utc_date > last_utc):
            account.last_checked = utc_date
            account.save(update_fields=['last_checked'])

    def _process_single_email(self, conn, email_id, llm_parse_email):
        from apps.transactions.models import Transaction
        status, msg_data = conn.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None
        raw_msg = msg_data[0][1]
        msg = email.message_from_bytes(raw_msg)
        from_header = self._decode_header(msg.get('From', ''))
        if not self._is_from_bank(from_header):
            return None
        msg_id = msg.get('Message-ID') or f'{self.account.id}:{email_id.decode()}'
        if Transaction.objects.filter(raw_email_id=msg_id).exists():
            logger.debug('Email duplicado: %s', msg_id)
            return None
        subject = self._decode_header(msg.get('Subject', ''))
        body = self.extract_text_from_email(msg)
        if self.is_subject_supported(subject):
            from .llm import LLMServiceError
            try:
                parsed_data = asyncio.run(llm_parse_email(subject, body))
            except LLMServiceError as e:
                _pause_polling_on_llm_error(str(e))
                raise
            return self._create_email_data(msg, parsed_data)
        return None


def _pause_polling_on_llm_error(reason: str):
    from apps.accounts.models import SystemState
    from django.utils import timezone as dj_timezone
    state = SystemState.get()
    state.polling_paused = True
    state.paused_reason = reason
    state.paused_at = dj_timezone.now()
    state.admin_notified = False
    state.save(update_fields=['polling_paused', 'paused_reason', 'paused_at', 'admin_notified'])
    logger.error('Polling pausado por error LLM: %s', reason)


def poll_once():
    from apps.accounts.models import Account, SystemState
    from apps.transactions.models import Transaction, TelegramNotification
    from apps.users.models import CustomUser

    state = SystemState.get()
    if state.polling_paused:
        logger.info('Polling pausado. Esperando reanudación admin.')
        return []

    accounts = Account.objects.filter(enabled=True)
    if not accounts.exists():
        logger.warning('No hay cuentas habilitadas')
        return []

    all_new = []
    for account in accounts:
        try:
            processor = EmailProcessor(account)
            new_emails = processor.process_emails()
            for email_data in new_emails:
                # Get user for this account
                user = account.users.filter(telegram_chat_id__isnull=False).first() or account.users.first()
                if not user:
                    logger.warning('Cuenta %s sin usuarios', account.id)
                    continue
                # Create transaction
                tx = Transaction.objects.create(
                    user=user,
                    date=email_data['date'],
                    amount=email_data['amount'],
                    merchant=email_data['merchant'],
                    type=email_data['type'],
                    category_name=email_data['suggested_category'],
                    raw_email_id=email_data['email_id'],
                )
                all_new.append(tx)
                # Outbox: create notification instead of using Queue
                TelegramNotification.objects.create(user=user, transaction=tx)
                logger.info('Nueva transaccion creada: tx_id=%s', tx.id)
        except Exception as e:
            logger.exception('Error procesando cuenta %s: %s', account.id, e)
    return all_new


def run_poller():
    logger.info('Iniciando email poller (intervalo %ss)', settings.POLL_INTERVAL)
    while True:
        try:
            new_txs = poll_once()
            if new_txs:
                logger.info('Total nuevas transacciones: %d', len(new_txs))
            time.sleep(settings.POLL_INTERVAL)
        except Exception as e:
            logger.exception('Error en poller: %s', e)
            time.sleep(settings.POLL_INTERVAL)
