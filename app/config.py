import os
from dotenv import load_dotenv

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
