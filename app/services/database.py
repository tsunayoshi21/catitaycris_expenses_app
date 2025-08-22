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

    # --- Nuevos métodos para centralizar lógica usada en routes.py ---
    @staticmethod
    def get_user_by_username(username: str):
        """Obtiene un usuario por su nombre de usuario.

        Args:
            username: Nombre de usuario.
        Returns:
            Instancia de User o None si no existe.
        """
        from ..models import User
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_transactions_for_user(user_id: int, q: str = '', category: str = '', ttype: str = None,
                                  start=None, end=None, limit: int = 2000):
        """Obtiene transacciones filtradas para un usuario.

        Aplica filtros por rango de fechas, categoría (case-insensitive), tipo y
        ordena por fecha descendente. El filtro de búsqueda libre `q` se aplica
        en memoria para mantener compatibilidad entre motores (SQLite/Postgres).

        Args:
            user_id: ID del usuario propietario de las transacciones.
            q: Texto de búsqueda libre (opcional, minúsculas recomendado).
            category: Categoría a buscar (case-insensitive).
            ttype: Tipo de transacción exacto.
            start: datetime de inicio (UTC) inclusive.
            end: datetime de término (UTC) exclusivo.
            limit: Límite de filas a retornar.
        Returns:
            Lista de instancias Transaction.
        """
        from ..models import Transaction

        query = Transaction.query.filter_by(user_id=user_id)
        if start and end:
            query = query.filter(Transaction.date >= start, Transaction.date < end)
        if category:
            query = query.filter(db.func.lower(Transaction.category).contains(category))
        if ttype:
            query = query.filter(Transaction.type == ttype)

        txs = query.order_by(Transaction.date.desc()).limit(limit).all()

        if q:
            q_norm = (q or '').strip().lower()
            def match_q(t):
                blob = f"{t.merchant or ''} {t.description or ''} {t.category or ''} {t.type or ''}".lower()
                return q_norm in blob
            txs = [t for t in txs if match_q(t)]
        return txs

    @staticmethod
    def update_transaction_for_user(user_id: int, transaction_id: int, description=None, category=None):
        """Actualiza una transacción si pertenece al usuario dado.

        Args:
            user_id: ID del usuario que posee la transacción.
            transaction_id: ID de la transacción a actualizar.
            description: Nueva descripción (puede ser None o cadena vacía).
            category: Nueva categoría (puede ser None o cadena vacía).
        Returns:
            La instancia actualizada de Transaction o None si no se encontró o no
            pertenece al usuario.
        """
        from ..models import Transaction
        tx = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
        if not tx:
            return None
        if description is not None:
            tx.description = (description or '').strip() or None
        if category is not None:
            tx.category = (category or '').strip() or None
        db.session.commit()
        return tx
