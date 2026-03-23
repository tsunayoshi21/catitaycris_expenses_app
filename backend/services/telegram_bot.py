import asyncio
import logging
import re

from django.conf import settings
from asgiref.sync import sync_to_async
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from apps.users.models import CustomUser
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if not user:
        await update.message.reply_text('No estas registrado. Contacta al admin.')
        return
    await update.message.reply_text('Bot activado. Te notificare sobre nuevas transacciones automaticamente.')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from apps.users.models import CustomUser
    from apps.transactions.models import Transaction, TelegramNotification
    from services.llm import categorize

    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()

    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if not user:
        await update.message.reply_text('No estas registrado. Contacta al administrador.')
        return

    replied = getattr(update.message, 'reply_to_message', None)
    if replied and replied.from_user and replied.from_user.is_bot:
        original_text = replied.text or ''
        m = re.search(r'#(\d+)', original_text)
        if not m:
            await update.message.reply_text('No pude identificar la transaccion.')
            return
        tx_id = int(m.group(1))

        tx = await sync_to_async(
            lambda: Transaction.objects.filter(id=tx_id, user=user).first()
        )()
        if not tx:
            await update.message.reply_text('Transaccion no encontrada o no autorizada.')
            return

        category = await categorize(text, tx.merchant, user_id=user.id)

        def _update_tx():
            tx.description = text
            tx.category_name = category
            tx.save(update_fields=['description', 'category_name', 'updated_at'])

        await sync_to_async(_update_tx)()
        await update.message.reply_text(
            f'Transaccion #{tx_id} guardada:\n'
            f'Descripcion: {text}\n'
            f'Categoria: {category}'
        )
        return

    await update.message.reply_text(
        'Para registrar una descripcion, responde directamente al mensaje de la transaccion.'
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception('Error en Telegram bot: %s', context.error)


async def resume_polling_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from apps.users.models import CustomUser
    from apps.accounts.models import SystemState

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(
        lambda: CustomUser.objects.filter(telegram_chat_id=chat_id).first()
    )()
    if not user or not user.is_staff:
        await update.message.reply_text('No tenés permisos para esto.')
        return
    state = await sync_to_async(SystemState.get)()
    state.polling_paused = False
    state.paused_reason = ''
    state.admin_notified = False
    await sync_to_async(state.save)(update_fields=['polling_paused', 'paused_reason', 'admin_notified'])
    await update.message.reply_text('✅ Polling reanudado.')


async def process_notification_outbox(application):
    """Poll TelegramNotification outbox and send pending notifications."""
    from apps.transactions.models import TelegramNotification
    from apps.users.models import CustomUser
    from apps.accounts.models import SystemState
    from django.utils import timezone as dj_timezone

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

            pending = await sync_to_async(
                lambda: list(
                    TelegramNotification.objects
                    .filter(sent=False)
                    .select_related('user', 'transaction')
                    .order_by('created_at')[:10]
                )
            )()
            for notif in pending:
                try:
                    tx = notif.transaction
                    user = notif.user
                    if not user.telegram_chat_id:
                        continue
                    msg = (
                        f'Nueva transaccion detectada (#{tx.id}):\n\n'
                        f'Fecha: {tx.date.strftime("%d/%m/%Y %H:%M")}\n'
                        f'Monto: ${tx.amount:,.0f}\n'
                        f'Comercio: {tx.merchant or "No especificado"}\n'
                        f'Tipo: {tx.type}\n'
                        f'Categoria sugerida: {tx.category_name or "sin categoria"}\n\n'
                        f'Por favor, escribe una breve descripcion de esta transaccion:'
                    )
                    await application.bot.send_message(
                        chat_id=user.telegram_chat_id,
                        text=msg + f'\n\nResponde a ESTE mensaje con la descripcion para la transaccion #{tx.id}',
                        reply_markup=ForceReply(
                            selective=True,
                            input_field_placeholder=f'Descripcion para #{tx.id}'
                        )
                    )

                    def _mark_sent():
                        notif.sent = True
                        notif.sent_at = dj_timezone.now()
                        notif.save(update_fields=['sent', 'sent_at'])

                    await sync_to_async(_mark_sent)()
                    logger.info('Notificacion enviada: tx_id=%s chat_id=%s', tx.id, user.telegram_chat_id)
                except Exception as e:
                    logger.error('Error enviando notificacion %s: %s', notif.id, e)
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
    application.add_handler(CommandHandler('resume_polling', resume_polling_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    outbox_task = asyncio.create_task(process_notification_outbox(application))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info('Bot de Telegram iniciado')

    await outbox_task  # runs forever
