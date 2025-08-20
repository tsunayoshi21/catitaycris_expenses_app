import os
from dotenv import load_dotenv
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()


class AppOnlyFilter(logging.Filter):
    """Filtro que solo permite logs de nuestros módulos de la aplicación"""
    def filter(self, record):
        # Solo permitir logs que empiecen con 'app.' o '__main__'
        return (
            record.name.startswith('app.')
            or record.name == '__main__'
            or record.name.startswith('__main__')
        )


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///finanzas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    IMAP_HOST = os.getenv('IMAP_HOST')
    IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
    IMAP_FOLDER = os.getenv('IMAP_FOLDER', 'INBOX')
    APP_ENCRYPTION_KEY = os.getenv('APP_ENCRYPTION_KEY')
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '60'))  # seconds
    _senders = (os.getenv('BANK_SENDERS') or '').strip().lower()
    ALLOWED_BANK_SENDERS = [s.strip() for s in _senders.split(',') if s.strip()]

    # Seguridad de cookies y sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    REMEMBER_COOKIE_HTTPONLY = True
    # Habilitar secure cookie solo si estamos detrás de HTTPS (configurable)
    HTTPS_ONLY = os.getenv('HTTPS_ONLY', '0') == '1'
    SESSION_COOKIE_SECURE = HTTPS_ONLY
    REMEMBER_COOKIE_SECURE = HTTPS_ONLY

    # Duración de sesión (sin "remember me")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_HOURS', '8')))
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https' if HTTPS_ONLY else 'http')

    @staticmethod
    def configure_logging():
        """Configura el logging global para toda la aplicación."""
        level_name = os.getenv('LOG_LEVEL', 'DEBUG').upper()
        level = getattr(logging, level_name, logging.INFO)

        # Configurar el logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capturar todo, filtrado por handlers

        # Evitar duplicados
        if root_logger.handlers:
            root_logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

        # File handler - solo logs de nuestra app
        file_handler = RotatingFileHandler('finanzas_app.log', maxBytes=1_000_000, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        file_handler.addFilter(AppOnlyFilter())
        root_logger.addHandler(file_handler)

        # Stream handler (stdout) - solo logs de nuestra app
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        stream_handler.addFilter(AppOnlyFilter())
        root_logger.addHandler(stream_handler)

        # Configurar loggers específicos para nuestros módulos
        app_loggers = [
            '__main__',
            'app.services.email_poller',
            'app.services.telegram_bot',
            'app.services.database',
            'app.services.llm',
            'app.routes',
            'app.models',
        ]
        for logger_name in app_loggers:
            logging.getLogger(logger_name).setLevel(level)

        # Silenciar loggers ruidosos de librerías externas
        noisy_loggers = [
            'httpcore',
            'httpx',
            'telegram',
            'telegram.ext',
            'urllib3',
            'requests',
            'asyncio',
            'werkzeug',
        ]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.ERROR)

        logging.getLogger(__name__).info(
            "Logging configurado - nivel: %s, filtrado solo app", level_name
        )
