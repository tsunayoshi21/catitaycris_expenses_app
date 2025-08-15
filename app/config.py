import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

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
