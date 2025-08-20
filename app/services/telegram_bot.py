import os
from threading import Thread
from queue import Queue, Empty
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from ..config import Config
from ..models import User
from .database import DatabaseManager
from .llm import categorize
import asyncio
import logging
import re

# Logger para este módulo
logger = logging.getLogger(__name__)

notification_queue = Queue()  # Queue para envío thread-safe


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flask_app = context.application.bot_data.get('flask_app')
    if not flask_app:
        return
    with flask_app.app_context():
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or "sin_username"
        logger.info('📱 Comando /start recibido de chat_id=%s username=%s', chat_id, username)
        
        user = User.query.filter_by(chat_id=chat_id).first()
        if not user:
            logger.warning('❌ Usuario chat_id=%s no registrado', chat_id)
            await update.message.reply_text('No estás registrado. Contacta al admin.')
            return
        
        logger.info('✅ Usuario %s (chat_id=%s) activó el bot', user.username, chat_id)
        await update.message.reply_text('🤖 Bot activado. Te notificaré sobre nuevas transacciones automáticamente.')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flask_app = context.application.bot_data.get('flask_app')
    if not flask_app:
        return
    with flask_app.app_context():
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or "sin_username"
        message_text = update.message.text.strip()
        
        logger.info('📨 Mensaje recibido de chat_id=%s username=%s: "%s"', 
                               chat_id, username, message_text[:100])
        
        # Auto-registrar usuario si envía mensaje pero no está registrado
        user = User.query.filter_by(chat_id=chat_id).first()
        if not user:
            logger.warning('❌ Usuario chat_id=%s no registrado, enviando mensaje de registro', chat_id)
            await update.message.reply_text(
                '👋 ¡Hola! Te he detectado automáticamente.\n'
                'Pero no estás registrado. Contacta al administrador para registrarte.'
            )
            return
        
        logger.debug('👤 Usuario encontrado: %s (id=%s)', user.username, user.id)
        
        text = update.message.text.strip()
        
        # Nuevo flujo: usar reply_to_message para identificar la transacción (#<id>)
        replied = getattr(update.message, 'reply_to_message', None)
        if replied and replied.from_user and replied.from_user.is_bot:
            original_text = replied.text or ''
            m = re.search(r'#(\d+)', original_text)
            if not m:
                logger.warning('❌ No se encontró tx_id en el mensaje referenciado por chat_id=%s', chat_id)
                await update.message.reply_text('❌ No pude identificar la transacción. Responde al mensaje del bot que contiene el ID (#123).')
                return
            tx_id = int(m.group(1))
            logger.info('💳 Procesando respuesta para transacción tx_id=%s del usuario=%s', tx_id, user.username)
            
            # Categorizar respuesta del usuario
            logger.debug('🤖 Categorizando respuesta: "%s"', text)
            category = categorize(text)
            logger.debug('📁 Categoría asignada: "%s"', category)
            
            # Actualizar transacción (la validación de pertenencia debería ocurrir en capa de DB)
            tx = DatabaseManager.update_transaction_description(tx_id, text, category)
            if tx:
                logger.info('✅ Transacción tx_id=%s actualizada - descripción="%s" categoría="%s"', tx_id, text, category)
                await update.message.reply_text(
                    f'✅ Transacción #{tx_id} guardada:\n'
                    f'💬 Descripción: {text}\n'
                    f'📁 Categoría: {category}'
                )
            else:
                logger.error('❌ Error: transacción tx_id=%s no encontrada en DB o no pertenece al usuario', tx_id)
                await update.message.reply_text('❌ Error: transacción no encontrada o no autorizada.')
            return
        
        # Si no es una respuesta a un mensaje del bot con #id, guiar al usuario
        logger.debug('💡 Mensaje sin referencia válida a transacción para chat_id=%s', chat_id)
        await update.message.reply_text(
            '💡 Para registrar una descripción, responde directamente al mensaje de la transacción que contiene el ID (por ejemplo, #123).'
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
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
            
            logger.debug("📤 Procesando notificación para chat_id=%s tx_id=%s", chat_id, transaction_id)
            
            # Enviar mensaje con ForceReply para facilitar la respuesta directa
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=message + "\n\n✍️ Responde a ESTE mensaje con la descripción para la transacción #" + str(transaction_id),
                    reply_markup=ForceReply(selective=True, input_field_placeholder=f"Descripción para #" + str(transaction_id))
                )
                logger.info("✅ Notificación enviada exitosamente a chat_id=%s", chat_id)
            except Exception as e:
                logger.error("❌ Error enviando mensaje a chat_id=%s: %s", chat_id, e)
                
        except Exception as e:
            logger.error("❌ Error procesando cola de notificaciones: %s", e)
            await asyncio.sleep(1.0)


def notify_new_transaction(app, transaction):
    """Notifica al usuario sobre una nueva transacción para que la describa"""
    with app.app_context():
        user = transaction.user
        if not user.chat_id:
            logger.warning('❌ Usuario %s (id=%s) sin chat_id configurado', user.username, user.id)
            return
        
        logger.info('📲 Preparando notificación para usuario=%s chat_id=%s tx_id=%s', 
                       user.username, user.chat_id, transaction.id)
        
        # Crear mensaje informativo incluyendo #<id>
        msg = (
            f"💳 Nueva transacción detectada (#"+str(transaction.id)+"):\n\n"
            f"📅 Fecha: {transaction.date.strftime('%d/%m/%Y %H:%M')}\n"
            f"💰 Monto: ${transaction.amount:,.0f}\n"
            f"🏪 Comercio: {transaction.merchant or 'No especificado'}\n"
            f"🔄 Tipo: {transaction.type}\n"
            f"📁 Categoría sugerida: {transaction.category}\n\n"
            f"❓ Por favor, escribe una breve descripción de esta transacción:"
        )
        
        logger.debug('📄 Mensaje creado (longitud=%d chars): %s...', 
                        len(msg), msg[:100])
        
        # Agregar a la cola thread-safe
        notification_data = {
            'chat_id': user.chat_id,
            'message': msg,
            'transaction_id': transaction.id
        }
        
        try:
            notification_queue.put(notification_data, timeout=1.0)
            logger.info('✅ Notificación agregada a cola - chat_id=%s tx_id=%s queue_size=%d', 
                           user.chat_id, transaction.id, notification_queue.qsize())
        except Exception as e:
            logger.error('❌ Error agregando notificación a cola para chat_id=%s: %s', 
                           user.chat_id, e)


def build_and_run_bot(app):
    """Inicializa y ejecuta el bot de Telegram"""
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('❌ TELEGRAM_BOT_TOKEN no configurado')
        return None
    
    logger.info('🚀 Configurando bot de Telegram...')
    
    def _run_bot():
        """Ejecuta el bot en un hilo separado"""
        async def _async_main():
            logger.info('🔧 Inicializando aplicación Telegram...')
            application = ApplicationBuilder().token(token).build()
            application.bot_data['flask_app'] = app
            
            # Registrar handlers
            application.add_handler(CommandHandler('start', start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            application.add_error_handler(error_handler)
            
            # Guardar referencia en la app
            app.config['TELEGRAM_APP'] = application
            
            logger.info('🤖 Iniciando bot de Telegram...')
            
            # Iniciar procesamiento de cola en paralelo
            logger.info('📤 Iniciando procesador de cola de notificaciones...')
            queue_task = asyncio.create_task(process_notification_queue(application))
            
            try:
                # Iniciar polling
                logger.info('🔄 Iniciando polling de Telegram...')
                await application.initialize()
                await application.start()
                await application.updater.start_polling()
                
                logger.info('✅ Bot de Telegram iniciado correctamente')
                
                # Mantener corriendo
                await queue_task
                
            except Exception as e:
                logger.exception('❌ Error en bot de Telegram: %s', e)
            finally:
                logger.info('🔄 Deteniendo bot de Telegram...')
                await application.stop()
                await application.shutdown()
                logger.info('✅ Bot de Telegram detenido')
        
        # Ejecutar loop asíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_async_main())
        except Exception as e:
            logger.exception('❌ Error en loop del bot: %s', e)
        finally:
            loop.close()
    
    # Ejecutar en hilo daemon
    logger.info('🧵 Iniciando hilo del bot de Telegram...')
    bot_thread = Thread(target=_run_bot, daemon=True)
    bot_thread.start()
    
    return bot_thread
