#!/usr/bin/env python3
"""Script de prueba para verificar acceso IMAP y listar nuevos correos del Banco de Chile.

Uso:
  export IMAP_HOST=outlook.office365.com
  export IMAP_USER="tu_usuario"
  export IMAP_PASSWORD="tu_password"
  python scripts/test_imap_watch.py

Parámetros opcionales (vars de entorno):
  IMAP_FOLDER (default INBOX)
  IMAP_PORT (default 993)
  LOOP=1  -> si es 1 hace polling continuo cada 30s

Salida: imprime asunto, remitente, fecha y primeras líneas del cuerpo para correos no vistos.
No modifica la base de datos.
"""
import os
import imaplib
import email
import time
from email.header import decode_header

HOST = os.getenv('IMAP_HOST', 'outlook.office365.com')
PORT = int(os.getenv('IMAP_PORT', '993'))
USER = os.getenv('IMAP_USER')
PASSWORD = os.getenv('IMAP_PASSWORD')
FOLDER = os.getenv('IMAP_FOLDER', 'INBOX')
LOOP = os.getenv('LOOP', '0') == '1'
INTERVAL = int(os.getenv('INTERVAL', '30'))

BANK_SENDERS = [
    'enviodigital@bancochile.cl',
    'serviciodetransferencias@bancochile.cl'
]


def decode_value(val):
    if not val:
        return ''
    parts = decode_header(val)
    decoded = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                decoded.append(text.decode(enc or 'utf-8', errors='ignore'))
            except Exception:
                decoded.append(text.decode('utf-8', errors='ignore'))
        else:
            decoded.append(text)
    return ''.join(decoded)


def fetch_unseen(conn):
    status, data = conn.search(None, 'UNSEEN')
    if status != 'OK':
        print('Busqueda UNSEEN falló')
        return []
    ids = data[0].split()
    return ids


def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain':
                try:
                    return part.get_payload(decode=True).decode(errors='ignore')
                except Exception:
                    continue
    else:
        try:
            return msg.get_payload(decode=True).decode(errors='ignore')
        except Exception:
            pass
    return ''


def process_once():
    print('Conectando a IMAP', f"{HOST}:{PORT}", 'folder', FOLDER)
    conn = imaplib.IMAP4_SSL(HOST, PORT)
    conn.login(USER, PASSWORD)
    conn.select(FOLDER)

    ids = fetch_unseen(conn)
    if not ids:
        print('No hay correos UNSEEN')
    for i, eid in enumerate(ids, 1):
        status, msg_data = conn.fetch(eid, '(RFC822)')
        if status != 'OK':
            print('No se pudo leer id', eid)
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        from_h = decode_value(msg.get('From'))
        subj = decode_value(msg.get('Subject'))
        date_h = msg.get('Date')
        body = get_body(msg)

        from_l = from_h.lower()
        is_bank = any(s in from_l for s in BANK_SENDERS)
        print('-'*60)
        print(f'ID: {eid.decode()}  BANK_MATCH={is_bank}')
        print('From   :', from_h)
        print('Subject:', subj)
        print('Date   :', date_h)
        print('Body (primeras 15 líneas):')
        for line in body.splitlines()[:15]:
            print('  ', line[:200])
    conn.logout()


if __name__ == '__main__':
    if not USER or not PASSWORD:
        print('Faltan IMAP_USER o IMAP_PASSWORD en entorno')
        raise SystemExit(1)
    try:
        if LOOP:
            while True:
                process_once()
                time.sleep(INTERVAL)
        else:
            process_once()
    except KeyboardInterrupt:
        print('Interrumpido por usuario')
