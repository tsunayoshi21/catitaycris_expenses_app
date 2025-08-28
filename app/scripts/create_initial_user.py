#!/usr/bin/env python3
"""Script para crear la cuenta y usuario inicial.
Usa variables de entorno y solicita datos sensibles si faltan.

Requisitos previos:
  - Exportar APP_ENCRYPTION_KEY (clave Fernet base64 url-safe de 32 bytes)
  - Exportar (opcional) DATABASE_URL si no se usa la default

Ejemplo:
  export APP_ENCRYPTION_KEY="<clave>"
  export IMAP_HOST="outlook.office365.com"
  # Forma recomendada:
  python -m app.scripts.create_initial_user --imap-user tu_usuario_imap \
     --imap-password 'tu_pass' --username admin --password 'pass_seguro' --chat-id 123456789
"""
import argparse
import getpass
import os
import sys
import pathlib

# Asegurar que el root del proyecto esté en sys.path aunque se ejecute dentro de app/scripts
ROOT = pathlib.Path(__file__).resolve().parents[2]  # .../APP_finanzas
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from main import create_app  # type: ignore
except ModuleNotFoundError as e:
    raise SystemExit(f"No se pudo importar main.py. Ejecuta el script desde la raíz del proyecto o usa: python -m app.scripts.create_initial_user\nDetalle: {e}")

from app.services.database import db
from app.models import Account, User


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--imap-host', default=os.getenv('IMAP_HOST') or 'outlook.office365.com')
    p.add_argument('--imap-user')
    p.add_argument('--imap-password')
    p.add_argument('--username', default='admin')
    p.add_argument('--password')
    p.add_argument('--chat-id', help='Chat ID de Telegram para recibir notificaciones')
    return p.parse_args()


def main():
    if not os.getenv('APP_ENCRYPTION_KEY'):
        raise SystemExit('Falta APP_ENCRYPTION_KEY en entorno')
    args = parse_args()

    imap_user = args.imap_user or input('IMAP user: ').strip()
    imap_password = args.imap_password or getpass.getpass('IMAP password: ')
    username = args.username
    pwd = args.password or getpass.getpass('Password usuario: ')

    app = create_app(start_services=False)
    with app.app_context():
        # if Account.query.first():
        #     print('Ya existe una cuenta. Abortando para evitar duplicados.')
        #     return
        acc = Account(imap_host=args.imap_host)
        acc.set_imap_credentials(imap_user, imap_password)
        user = User(username=username, account=acc, chat_id=args.chat_id)
        user.set_password(pwd)
        db.session.add_all([acc, user])
        db.session.commit()
        print('Cuenta y usuario creados OK.')
        print(f'Usuario: {username}  ChatID: {args.chat_id}')

if __name__ == '__main__':
    main()
