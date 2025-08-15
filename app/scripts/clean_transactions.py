#!/usr/bin/env python3
"""
Script para limpiar la tabla de transacciones durante las pruebas.
Uso: python -m app.scripts.clean_transactions
"""

import os
import sys
from datetime import datetime

# Agregar el directorio padre al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import db
from app.models import Transaction
from main import create_app


def clean_transactions():
    """Elimina todas las transacciones de la base de datos"""
    app = create_app(start_services=False)
    
    with app.app_context():
        print("🧹 Limpiando tabla de transacciones...")
        
        # Contar transacciones existentes
        count_before = Transaction.query.count()
        print(f"📊 Transacciones encontradas: {count_before}")
        
        if count_before == 0:
            print("✅ No hay transacciones para eliminar.")
            return
        
        # Confirmar eliminación
        response = input(f"❓ ¿Eliminar {count_before} transacciones? (s/N): ").strip().lower()
        
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return
        
        # Eliminar todas las transacciones
        try:
            deleted = db.session.query(Transaction).delete()
            db.session.commit()
            
            print(f"✅ {deleted} transacciones eliminadas correctamente.")
            print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error eliminando transacciones: {e}")
            return
        
        # Verificar que se eliminaron
        count_after = Transaction.query.count()
        if count_after == 0:
            print("🎉 Tabla de transacciones limpia.")
        else:
            print(f"⚠️  Aún quedan {count_after} transacciones.")


def clean_with_filters():
    """Elimina transacciones con filtros específicos"""
    app = create_app(start_services=False)
    
    with app.app_context():
        print("🧹 Limpieza avanzada de transacciones...")
        print("Opciones:")
        print("1. Eliminar por usuario")
        print("2. Eliminar por fecha")
        print("3. Eliminar por tipo")
        print("4. Eliminar todas")
        
        choice = input("Selecciona opción (1-4): ").strip()
        
        query = Transaction.query
        
        if choice == "1":
            user_id = input("ID de usuario: ").strip()
            if user_id.isdigit():
                query = query.filter_by(user_id=int(user_id))
            else:
                print("❌ ID de usuario inválido.")
                return
                
        elif choice == "2":
            date_str = input("Fecha (YYYY-MM-DD): ").strip()
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Transaction.date) == date_obj)
            except ValueError:
                print("❌ Formato de fecha inválido.")
                return
                
        elif choice == "3":
            tx_type = input("Tipo (debito/credito/transferencia): ").strip()
            query = query.filter_by(type=tx_type)
            
        elif choice == "4":
            query = Transaction.query
            
        else:
            print("❌ Opción inválida.")
            return
        
        # Contar y confirmar
        count = query.count()
        print(f"📊 Transacciones a eliminar: {count}")
        
        if count == 0:
            print("✅ No hay transacciones que coincidan con los criterios.")
            return
        
        response = input(f"❓ ¿Eliminar {count} transacciones? (s/N): ").strip().lower()
        
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return
        
        try:
            deleted = query.delete()
            db.session.commit()
            print(f"✅ {deleted} transacciones eliminadas.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpia la tabla de transacciones")
    parser.add_argument("--advanced", "-a", action="store_true", 
                       help="Modo avanzado con filtros")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Forzar eliminación sin confirmación")
    
    args = parser.parse_args()
    
    if args.advanced:
        clean_with_filters()
    else:
        if args.force:
            # Modo forzado para scripts automatizados
            app = create_app(start_services=False)
            with app.app_context():
                deleted = db.session.query(Transaction).delete()
                db.session.commit()
                print(f"✅ {deleted} transacciones eliminadas (modo forzado).")
        else:
            clean_transactions()
