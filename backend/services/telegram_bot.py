import asyncio
import logging
import re
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from django.utils import timezone as dj_timezone

from apps.accounts.models import SystemState
from apps.transactions.models import Transaction, TelegramNotification, Category
from apps.users.models import CustomUser
from services.llm import categorize

logger = logging.getLogger(__name__)


def format_amount(currency, amount, amount_clp, fx_status):
    """Formatea el monto para notificaciones: USD con 2 decimales + equivalente CLP; CLP entero."""
    if currency == 'USD':
        s = f'US${amount:,.2f}'
        if amount_clp is not None:
            prefix = '≈ ' if fx_status == 'estimated' else ''
            s += f' ({prefix}${amount_clp:,.0f} CLP)'
        return s
    return f'${amount:,.0f} CLP'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    logger.info('Comando /start recibido de chat_id=%s', chat_id)
    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if user:
        await update.message.reply_text(
            f'Hola {user.username}! Ya estas vinculado. '
            f'Te notificare sobre nuevas transacciones automaticamente.'
        )
        return
    await update.message.reply_text(
        'Hola! Para vincular tu cuenta, segui estos pasos:\n\n'
        '1. Abri Ajustes en la app web\n'
        '2. Genera tu token de vinculacion\n'
        '3. Escribi aca: /vincular <tu_token>'
    )


async def vincular_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        await update.message.reply_text(
            'Uso: /vincular <token>\n\n'
            'Encontra tu token en la seccion Ajustes de la app web.'
        )
        return

    token = args[0].strip()
    logger.info('/vincular recibido de chat_id=%s', chat_id)

    existing = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if existing:
        await update.message.reply_text(
            f'Este Telegram ya esta vinculado al usuario "{existing.username}". '
            f'Desvinculalo primero desde Ajustes en la web.'
        )
        return

    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_link_token=token).first()
    )()
    if not user:
        logger.warning('Token invalido de chat_id=%s', chat_id)
        await update.message.reply_text('Token invalido. Revisa que lo copiaste bien.')
        return

    def _link():
        user.telegram_chat_id = chat_id
        user.telegram_link_token = None
        user.telegram_link_token_created_at = None
        user.save(update_fields=[
            'telegram_chat_id', 'telegram_link_token', 'telegram_link_token_created_at',
        ])

    await sync_to_async(_link)()
    logger.info('Usuario %s vinculado a chat_id=%s', user.username, chat_id)
    await update.message.reply_text(
        f'✅ Listo! Tu cuenta "{user.username}" quedo vinculada.\n'
        f'Te notificare cuando se detecten nuevas transacciones.'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    logger.info('Mensaje recibido de chat_id=%s (longitud=%d)', chat_id, len(text))

    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if not user:
        logger.warning('Mensaje de usuario no registrado: chat_id=%s', chat_id)
        await update.message.reply_text('No estas registrado. Contacta al administrador.')
        return

    replied = getattr(update.message, 'reply_to_message', None)
    if replied and replied.from_user and replied.from_user.is_bot:
        original_text = replied.text or ''
        m = re.search(r'#(\d+)', original_text)
        if not m:
            logger.warning('No se pudo identificar transaccion en reply, chat_id=%s', chat_id)
            await update.message.reply_text('No pude identificar la transaccion.')
            return
        tx_id = int(m.group(1))

        tx = await sync_to_async(
            lambda: Transaction.objects.filter(id=tx_id, user=user).first()
        )()
        if not tx:
            logger.warning('Transaccion %s no encontrada para usuario chat_id=%s', tx_id, chat_id)
            await update.message.reply_text('Transaccion no encontrada o no autorizada.')
            return

        logger.info('Categorizando transaccion #%s con descripcion: %s', tx_id, text[:50])
        valid_cats = await sync_to_async(
            lambda: list(Category.get_valid_for_user(user.id).values_list('name', flat=True))
        )()
        category = await categorize(text, tx.merchant, user_id=user.id, valid_categories=valid_cats)
        logger.info('Categoria asignada para tx #%s: %s', tx_id, category)

        def _update_tx():
            cat_obj = Category.get_valid_for_user(user.id).filter(name=category).first()
            tx.description = text
            tx.category_name = category
            tx.category = cat_obj
            tx.save(update_fields=['description', 'category_name', 'category', 'updated_at'])

        await sync_to_async(_update_tx)()
        logger.info('Transaccion #%s actualizada: descripcion=%s, categoria=%s', tx_id, text[:50], category)
        await update.message.reply_text(
            f'✅ Transaccion #{tx_id} guardada:\n'
            f'📝 Descripcion: {text}\n'
            f'📁 Categoria: {category}'
        )
        return

    await update.message.reply_text(
        'Para registrar una descripcion, responde directamente al mensaje de la transaccion.'
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception('Error en Telegram bot: %s', context.error)


async def resume_polling_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    logger.info('Comando /resume_polling recibido de chat_id=%s', chat_id)
    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if not user or not user.is_staff:
        logger.warning('Intento de /resume_polling sin permisos: chat_id=%s', chat_id)
        await update.message.reply_text('No tenés permisos para esto.')
        return
    state = await sync_to_async(SystemState.get)()
    state.polling_paused = False
    state.paused_reason = ''
    state.admin_notified = False
    await sync_to_async(state.save)(update_fields=['polling_paused', 'paused_reason', 'admin_notified'])
    logger.info('Polling reanudado por admin chat_id=%s', chat_id)
    await update.message.reply_text('✅ Polling reanudado.')


async def process_notification_outbox(application):
    """Poll TelegramNotification outbox and send pending notifications.

    Uses SELECT FOR UPDATE SKIP LOCKED to prevent duplicate sends
    when multiple workers run concurrently (e.g. during container restarts).
    """
    STALE_LOCK_SECONDS = 120

    def _reclaim_stale():
        """Release claims from workers that crashed mid-send."""
        cutoff = dj_timezone.now() - timedelta(seconds=STALE_LOCK_SECONDS)
        TelegramNotification.objects.filter(
            sent=False, failed=False,
            processing_at__isnull=False,
            processing_at__lt=cutoff,
        ).update(processing_at=None)

    def _claim_pending():
        """Atomically claim pending notifications with row-level locking."""
        with transaction.atomic():
            pending = list(
                TelegramNotification.objects
                .filter(sent=False, failed=False, processing_at__isnull=True)
                .select_for_update(skip_locked=True)
                .select_related('user', 'transaction')
                .order_by('created_at')[:10]
            )
            now = dj_timezone.now()
            for notif in pending:
                notif.processing_at = now
                notif.save(update_fields=['processing_at'])
            return pending

    logger.info('Iniciando procesador de outbox de notificaciones...')
    while True:
        try:
            state = await sync_to_async(SystemState.get)()
            if state.polling_paused and not state.admin_notified:
                admins = await sync_to_async(
                    lambda: list(CustomUser.objects.filter(is_staff=True, telegram_chat_id__isnull=False))
                )()
                for admin in admins:
                    try:
                        await application.bot.send_message(
                            chat_id=admin.telegram_chat_id,
                            text=f'⚠️ Polling detenido por error LLM:\n{state.paused_reason}\n\nUsá /resume_polling para reanudar.'
                        )
                    except Exception as e:
                        logger.error('Error notificando admin %s: %s', admin.telegram_chat_id, e)
                state.admin_notified = True
                await sync_to_async(state.save)(update_fields=['admin_notified'])

            await sync_to_async(_reclaim_stale)()
            pending = await sync_to_async(_claim_pending)()

            for notif in pending:
                try:
                    tx = notif.transaction
                    user = notif.user
                    if not user.telegram_chat_id:
                        logger.warning(
                            'Notificacion %s omitida: usuario %s sin telegram_chat_id',
                            notif.id, user.id,
                        )

                        def _mark_skipped(n=notif):
                            n.sent = True
                            n.processing_at = None
                            n.save(update_fields=['sent', 'processing_at'])

                        await sync_to_async(_mark_skipped)()
                        continue
                    msg = (
                        f'💳 Nueva transaccion detectada (#{tx.id}):\n\n'
                        f'📅 Fecha: {tx.date.strftime("%d/%m/%Y %H:%M")}\n'
                        f'💰 Monto: {format_amount(tx.currency, tx.amount, tx.amount_clp, tx.fx_status)}\n'
                        f'🏪 Comercio: {tx.merchant or "No especificado"}\n'
                        f'🔄 Tipo: {tx.type}\n'
                        f'📁 Categoria sugerida: {tx.category_name or "sin categoria"}\n\n'
                        f'❓ Por favor, escribe una breve descripcion de esta transaccion:\n\n'
                        f'✍️ Responde a ESTE mensaje con la descripcion para la transaccion #{tx.id}'
                    )
                    await application.bot.send_message(
                        chat_id=user.telegram_chat_id,
                        text=msg,
                        reply_markup=ForceReply(
                            selective=True,
                            input_field_placeholder=f'Descripcion para #{tx.id}'
                        )
                    )

                    def _mark_sent(n=notif):
                        n.sent = True
                        n.sent_at = dj_timezone.now()
                        n.processing_at = None
                        n.save(update_fields=['sent', 'sent_at', 'processing_at'])

                    await sync_to_async(_mark_sent)()
                    logger.info('Notificacion enviada: tx_id=%s chat_id=%s', tx.id, user.telegram_chat_id)
                except Exception as e:
                    logger.error(
                        'Error enviando notificacion %s (intento %d): %s',
                        notif.id, notif.retry_count + 1, e,
                    )

                    def _mark_retry(n=notif, err=e):
                        n.retry_count += 1
                        n.last_error = str(err)[:500]
                        n.processing_at = None
                        if n.retry_count >= TelegramNotification.MAX_RETRIES:
                            n.failed = True
                            logger.warning(
                                'Notificacion %s marcada como fallida tras %d intentos',
                                n.id, n.retry_count,
                            )
                        n.save(update_fields=['retry_count', 'last_error', 'failed', 'processing_at'])

                    await sync_to_async(_mark_retry)()
        except Exception as e:
            logger.error('Error procesando outbox: %s', e)
        await asyncio.sleep(2)


async def build_and_run_bot():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN no configurado')
        return

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('vincular', vincular_cmd))
    application.add_handler(CommandHandler('resume_polling', resume_polling_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    outbox_task = asyncio.create_task(process_notification_outbox(application))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info('Bot de Telegram iniciado')

    await outbox_task  # runs forever
