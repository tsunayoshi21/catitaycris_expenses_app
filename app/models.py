from .services.database import db
from datetime import datetime, timezone
import os
import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from flask_login import UserMixin

# Utilidad de cifrado simétrico para credenciales sensibles (IMAP password)
# Generar clave una vez y ponerla en variable de entorno APP_ENCRYPTION_KEY (32 url-safe base64 bytes de Fernet)

def _get_fernet():
    key = os.getenv('APP_ENCRYPTION_KEY')
    if not key:
        # En ausencia de clave se lanza excepción para evitar guardar en claro
        raise RuntimeError('APP_ENCRYPTION_KEY faltante')
    return Fernet(key)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    imap_host = db.Column(db.String(255), nullable=False)
    imap_user_encrypted = db.Column(db.LargeBinary, nullable=False)
    imap_password_encrypted = db.Column(db.LargeBinary, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text('1'))
    last_checked = db.Column(db.DateTime(timezone.utc), default=lambda: datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc), server_default=db.text("'2025-08-01 00:00:00'"))  # Default 1 Aug 2025 UTC
    created_at = db.Column(db.DateTime(timezone.utc), default=datetime.now(timezone.utc))

    users = db.relationship('User', back_populates='account', cascade='all,delete')

    # Métodos helper para set/get seguros
    def set_imap_credentials(self, imap_user: str, imap_password: str):
        f = _get_fernet()
        self.imap_user_encrypted = f.encrypt(imap_user.encode())
        self.imap_password_encrypted = f.encrypt(imap_password.encode())

    def get_imap_credentials(self):
        f = _get_fernet()
        try:
            user = f.decrypt(self.imap_user_encrypted).decode()
            pw = f.decrypt(self.imap_password_encrypted).decode()
            return user, pw
        except InvalidToken:
            raise RuntimeError('No se pudo descifrar credenciales (clave incorrecta)')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    chat_id = db.Column(db.String(50), unique=True, index=True)  # ID de chat de Telegram
    created_at = db.Column(db.DateTime(timezone.utc), default=datetime.now(timezone.utc))

    account = db.relationship('Account', back_populates='users')
    transactions = db.relationship('Transaction', backref='user', cascade='all,delete', lazy='dynamic')

    def set_password(self, password: str):
        # bcrypt genera salt incorporado
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode(), self.password_hash)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone.utc), default=datetime.now(timezone.utc), index=True)
    amount = db.Column(db.Float, nullable=False)
    merchant = db.Column(db.String(255))
    type = db.Column(db.String(50))  # Debito / Credito / Transferencia
    description = db.Column(db.Text)  # User free-text answer
    category = db.Column(db.String(100))
    raw_email_id = db.Column(db.String(255), unique=True)  # UID or message-id to avoid duplicates
    created_at = db.Column(db.DateTime(timezone.utc), default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'amount': self.amount,
            'merchant': self.merchant,
            'type': self.type,
            'description': self.description,
            'category': self.category
        }
