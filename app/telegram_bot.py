import os
from threading import Thread
from queue import Queue, Empty
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from .config import Config
from .models import User
from .database import DatabaseManager
from .llm import categorize
from flask import current_app
import asyncio

pending_questions = {}  # chat_id -> transaction_id
notification_queue = Queue()  # Queue para envío thread-safe


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flask_app = context.application.bot_data.get('flask_app')
    if not flask_app:
        return
    with flask_app.app_context():
        chat_id = str(update.effective_chat.id)
        user = User.query.filter_by(chat_id=chat_id).first()
        if not user:
            await update.message.reply_text('No estás registrado. Contacta al admin.')
            return
        await update.message.reply_text('🤖 Bot activado. Te notificaré sobre nuevas transacciones automáticamente.')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flask_app = context.application.bot_data.get('flask_app')
    if not flask_app:
        return
    with flask_app.app_context():
        chat_id = str(update.effective_chat.id)
        
        # Auto-registrar usuario si envía mensaje pero no está registrado
        user = User.query.filter_by(chat_id=chat_id).first()
        if not user:
            await update.message.reply_text(
                '👋 ¡Hola! Te he detectado automáticamente.\n'
                'Ya puedes recibir notificaciones de transacciones.'
            )
            return
        
        text = update.message.text.strip()
        
        if chat_id in pending_questions:
            # Usuario respondió sobre una transacción pendiente
            tx_id = pending_questions.pop(chat_id)
            category = categorize(text)
            
            tx = DatabaseManager.update_transaction_description(tx_id, text, category)
            if tx:
                await update.message.reply_text(
                    f'✅ Transacción guardada:\n'
                    f'💬 Descripción: {text}\n'
                    f'📁 Categoría: {category}'
                )
            else:
                await update.message.reply_text('❌ Error: transacción no encontrada.')
        else:
            # Mensaje sin contexto - solo categorizar
            category = categorize(text)
            await update.message.reply_text(
                f'💡 No hay transacciones pendientes.\n'
                f'📁 Categoría sugerida para "{text}": {category}'
            )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    flask_app = context.application.bot_data.get('flask_app')
    logger = flask_app.logger if flask_app else current_app.logger
    logger.exception('Error en Telegram bot: update=%s error=%s', 
                    getattr(update, 'update_id', None), context.error)


async def process_notification_queue(application):
    """Procesa la cola de notificaciones de forma asíncrona"""
    while True:
        try:
            # Esperar por notificaciones en la cola
            try:
                notification_data = notification_queue.get(timeout=1.0)
            except Empty:
                await asyncio.sleep(0.1)
                continue
            
            chat_id = notification_data['chat_id']
            message = notification_data['message']
            transaction_id = notification_data['transaction_id']
            
            # Guardar transacción como pendiente
            pending_questions[chat_id] = transaction_id
            
            # Enviar mensaje
            try:
                await application.bot.send_message(chat_id=chat_id, text=message)
                print(f"✅ Notificación enviada a chat_id {chat_id}")
            except Exception as e:
                print(f"❌ Error enviando mensaje a {chat_id}: {e}")
                
        except Exception as e:
            print(f"❌ Error procesando cola: {e}")
            await asyncio.sleep(1.0)


def notify_new_transaction(app, transaction):
    """Notifica al usuario sobre una nueva transacción para que la describa"""
    with app.app_context():
        user = transaction.user
        if not user.chat_id:
            app.logger.warning('Usuario %s sin chat_id configurado', user.id)
            return
        
        # Crear mensaje informativo
        msg = (
            f"💳 Nueva transacción detectada:\n\n"
            f"📅 Fecha: {transaction.date.strftime('%d/%m/%Y %H:%M')}\n"
            f"💰 Monto: ${transaction.amount:,.0f}\n"
            f"🏪 Comercio: {transaction.merchant or 'No especificado'}\n"
            f"🔄 Tipo: {transaction.type}\n"
            f"📁 Categoría sugerida: {transaction.category}\n\n"
            f"❓ Por favor, escribe una breve descripción de esta transacción:"
        )
        
        # Agregar a la cola thread-safe
        notification_data = {
            'chat_id': user.chat_id,
            'message': msg,
            'transaction_id': transaction.id
        }
        
        try:
            notification_queue.put(notification_data, timeout=1.0)
            app.logger.debug('Notificación agregada a cola para chat_id %s', user.chat_id)
        except Exception as e:
            app.logger.error('Error agregando notificación a cola: %s', e)


def build_and_run_bot(app):
    """Inicializa y ejecuta el bot de Telegram"""
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        app.logger.warning('TELEGRAM_BOT_TOKEN no configurado')
        return None
    
    def _run_bot():
        """Ejecuta el bot en un hilo separado"""
        async def _async_main():
            application = ApplicationBuilder().token(token).build()
            application.bot_data['flask_app'] = app
            
            # Registrar handlers
            application.add_handler(CommandHandler('start', start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            application.add_error_handler(error_handler)
            
            # Guardar referencia en la app
            app.config['TELEGRAM_APP'] = application
            
            app.logger.info('🤖 Iniciando bot de Telegram...')
            
            # Iniciar procesamiento de cola en paralelo
            queue_task = asyncio.create_task(process_notification_queue(application))
            
            try:
                # Iniciar polling
                await application.initialize()
                await application.start()
                await application.updater.start_polling()
                
                # Mantener corriendo
                await queue_task
                
            except Exception as e:
                app.logger.exception('Error en bot de Telegram: %s', e)
            finally:
                await application.stop()
                await application.shutdown()
        
        # Ejecutar loop asíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_async_main())
        except Exception as e:
            app.logger.exception('Error en loop del bot: %s', e)
        finally:
            loop.close()
    
    # Ejecutar en hilo daemon
    bot_thread = Thread(target=_run_bot, daemon=True)
    bot_thread.start()
    
    return bot_thread
