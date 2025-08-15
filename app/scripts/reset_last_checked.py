#!/usr/bin/env python3
"""
Script para resetear la fecha last_checked de todas las cuentas al 1 de agosto de 2025.
Uso: python -m app.scripts.reset_last_checked
"""

import os
import sys
from datetime import datetime, timezone

# Agregar el directorio padre al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import db
from app.models import Account
from main import create_app


# Fecha de reset por defecto
DEFAULT_RESET_DATE = datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc)


def reset_last_checked(reset_date=None, force=False):
    """Resetea el last_checked de todas las cuentas"""
    if reset_date is None:
        reset_date = DEFAULT_RESET_DATE
    
    app = create_app(start_services=False)
    
    with app.app_context():
        print("🔄 Reseteando last_checked de cuentas...")
        print(f"📅 Fecha de reset: {reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Obtener todas las cuentas
        accounts = Account.query.all()
        
        if not accounts:
            print("⚠️  No se encontraron cuentas en la base de datos.")
            return
        
        print(f"📊 Cuentas encontradas: {len(accounts)}")
        
        # Mostrar estado actual
        print("\n📋 Estado actual:")
        for account in accounts:
            current_date = account.last_checked
            date_str = current_date.strftime('%Y-%m-%d %H:%M:%S UTC') if current_date else 'None'
            print(f"  • Cuenta {account.id} ({account.imap_host}): {date_str}")
        
        # Confirmar operación
        if not force:
            print(f"\n❓ ¿Resetear last_checked de {len(accounts)} cuentas a {reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}?")
            response = input("Confirmar (s/N): ").strip().lower()
            
            if response not in ['s', 'si', 'sí', 'y', 'yes']:
                print("❌ Operación cancelada.")
                return
        
        # Realizar el reset
        try:
            updated_count = 0
            
            for account in accounts:
                old_date = account.last_checked
                account.last_checked = reset_date
                updated_count += 1
                
                if not force:
                    old_str = old_date.strftime('%Y-%m-%d %H:%M:%S UTC') if old_date else 'None'
                    print(f"  ✅ Cuenta {account.id}: {old_str} → {reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Guardar cambios
            db.session.commit()
            
            print(f"\n🎉 {updated_count} cuentas actualizadas correctamente.")
            print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error actualizando cuentas: {e}")
            return


def reset_specific_accounts(account_ids, reset_date=None, force=False):
    """Resetea el last_checked de cuentas específicas"""
    if reset_date is None:
        reset_date = DEFAULT_RESET_DATE
    
    app = create_app(start_services=False)
    
    with app.app_context():
        print(f"🔄 Reseteando cuentas específicas: {account_ids}")
        print(f"📅 Fecha de reset: {reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Obtener cuentas específicas
        accounts = Account.query.filter(Account.id.in_(account_ids)).all()
        
        if not accounts:
            print("⚠️  No se encontraron cuentas con los IDs especificados.")
            return
        
        found_ids = [acc.id for acc in accounts]
        missing_ids = set(account_ids) - set(found_ids)
        
        if missing_ids:
            print(f"⚠️  Cuentas no encontradas: {list(missing_ids)}")
        
        print(f"📊 Cuentas a actualizar: {len(accounts)}")
        
        # Confirmar operación
        if not force:
            for account in accounts:
                current_date = account.last_checked
                date_str = current_date.strftime('%Y-%m-%d %H:%M:%S UTC') if current_date else 'None'
                print(f"  • Cuenta {account.id}: {date_str}")
            
            response = input(f"\n❓ ¿Resetear estas {len(accounts)} cuentas? (s/N): ").strip().lower()
            
            if response not in ['s', 'si', 'sí', 'y', 'yes']:
                print("❌ Operación cancelada.")
                return
        
        # Realizar el reset
        try:
            for account in accounts:
                old_date = account.last_checked
                account.last_checked = reset_date
                
                if not force:
                    old_str = old_date.strftime('%Y-%m-%d %H:%M:%S UTC') if old_date else 'None'
                    print(f"  ✅ Cuenta {account.id}: {old_str} → {reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            db.session.commit()
            print(f"\n🎉 {len(accounts)} cuentas actualizadas correctamente.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")


def list_accounts():
    """Lista todas las cuentas y sus fechas last_checked"""
    app = create_app(start_services=False)
    
    with app.app_context():
        accounts = Account.query.all()
        
        if not accounts:
            print("⚠️  No hay cuentas en la base de datos.")
            return
        
        print("📋 Estado actual de cuentas:")
        print("=" * 60)
        
        for account in accounts:
            date_str = account.last_checked.strftime('%Y-%m-%d %H:%M:%S UTC') if account.last_checked else 'None'
            enabled_str = "✅" if account.enabled else "❌"
            user_count = len(account.users)
            
            print(f"ID: {account.id}")
            print(f"Host: {account.imap_host}")
            print(f"Habilitada: {enabled_str}")
            print(f"Usuarios: {user_count}")
            print(f"Last checked: {date_str}")
            print("-" * 40)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Resetea last_checked de cuentas")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Forzar reset sin confirmación")
    parser.add_argument("--date", "-d", type=str,
                       help="Fecha personalizada (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--accounts", "-a", type=str,
                       help="IDs de cuentas específicas (ej: 1,2,3)")
    parser.add_argument("--list", "-l", action="store_true",
                       help="Listar estado actual de cuentas")
    
    args = parser.parse_args()
    
    if args.list:
        list_accounts()
        sys.exit(0)
    
    # Parsear fecha personalizada si se proporciona
    reset_date = DEFAULT_RESET_DATE
    if args.date:
        try:
            # Intentar parsear con hora
            reset_date = datetime.strptime(args.date, '%Y-%m-%d %H:%M:%S')
            reset_date = reset_date.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                # Intentar parsear solo fecha
                reset_date = datetime.strptime(args.date, '%Y-%m-%d')
                reset_date = reset_date.replace(tzinfo=timezone.utc)
            except ValueError:
                print("❌ Formato de fecha inválido. Usar: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS")
                sys.exit(1)
    
    # Parsear cuentas específicas si se proporcionan
    if args.accounts:
        try:
            account_ids = [int(x.strip()) for x in args.accounts.split(',')]
            reset_specific_accounts(account_ids, reset_date, args.force)
        except ValueError:
            print("❌ IDs de cuentas inválidos. Usar formato: 1,2,3")
            sys.exit(1)
    else:
        reset_last_checked(reset_date, args.force)
