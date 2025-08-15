from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import logging

# Logger para este módulo
logger = logging.getLogger(__name__)

db = SQLAlchemy()


class DatabaseManager:
    """Maneja todas las operaciones de base de datos"""
    
    @staticmethod
    def _ensure_utc(dt):
        """Convierte datetime a UTC para evitar comparaciones naive/aware"""
        if not dt:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def get_enabled_accounts():
        """Obtiene todas las cuentas habilitadas"""
        from ..models import Account
        return Account.query.filter_by(enabled=True).all()
    
    @staticmethod
    def is_duplicate_transaction(email_id):
        """Verifica si ya existe una transacción con este email ID"""
        from ..models import Transaction
        return Transaction.query.filter_by(raw_email_id=email_id).first() is not None
    
    @staticmethod
    def get_user_for_account(account):
        """Obtiene el primer usuario con chat_id para una cuenta"""
        return next((u for u in account.users if u.chat_id), 
                   account.users[0] if account.users else None)
    
    @staticmethod
    def create_pending_transaction(email_data, user):
        """Crea una transacción pendiente de confirmación del usuario"""
        from ..models import Transaction
        
        # Normalizar fecha a UTC
        date_utc = DatabaseManager._ensure_utc(email_data['date'])
        
        tx = Transaction(
            date=date_utc,
            amount=email_data['amount'],
            merchant=email_data['merchant'],
            type=email_data['type'],
            description=None,  # Será llenado por el usuario vía Telegram
            category=email_data['suggested_category'],
            raw_email_id=email_data['email_id'],
            user=user
        )
        db.session.add(tx)
        db.session.commit()
        return tx
    
    @staticmethod
    def update_last_checked(account, new_date):
        """Actualiza la fecha de última revisión de una cuenta"""
        new_date_utc = DatabaseManager._ensure_utc(new_date)
        last_checked_utc = DatabaseManager._ensure_utc(account.last_checked)
        
        if new_date_utc and (last_checked_utc is None or new_date_utc > last_checked_utc):
            account.last_checked = new_date_utc
            db.session.commit()
    
    @staticmethod
    def update_transaction_description(transaction_id, description, category):
        """Actualiza la descripción y categoría de una transacción"""
        from ..models import Transaction
        
        tx = Transaction.query.get(transaction_id)
        if tx:
            tx.description = description
            tx.category = category
            db.session.commit()
        return tx
