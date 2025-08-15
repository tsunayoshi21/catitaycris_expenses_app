import imaplib
import email
from email.header import decode_header
import time
from datetime import datetime, timezone
from .config import Config
from .database import DatabaseManager
from .llm import parse_email
from .telegram_bot import notify_new_transaction
from flask import current_app


class EmailProcessor:
    """Procesa emails de una cuenta IMAP"""
    
    def __init__(self, account):
        self.account = account
        self.imap_user, self.imap_password = account.get_imap_credentials()

    def is_subject_supported(self, subject):
        # Currently only support Banco de Chile emails
        # Currently only support charges and transfers, not incomes
        valid_subjects = ["Transferencia a Terceros",
                            "Cargo en Cuenta",
                            "Compra con Tarjeta de Crédito"]
        
        return subject in valid_subjects

    def _ensure_utc(self, dt):
        """Convierte datetime a UTC"""
        if not dt:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    def _decode_header(self, val):
        """Decodifica headers de email"""
        if not val:
            return ''
        parts = decode_header(val)
        out = []
        for txt, enc in parts:
            if isinstance(txt, bytes):
                try:
                    out.append(txt.decode(enc or 'utf-8', errors='ignore'))
                except Exception:
                    out.append(txt.decode('utf-8', errors='ignore'))
            else:
                out.append(txt)
        return ''.join(out)
    
    def _get_email_body(self, msg):
        """Extrae el cuerpo de texto del email, priorizando texto plano sobre HTML"""
        # Primero intentar obtener texto plano
        plain_text = self._get_plain_text_body(msg)
        if plain_text and len(plain_text.strip()) > 50:  # Si hay suficiente texto plano
            return plain_text
        
        # Si no hay texto plano suficiente, procesar HTML
        html_text = self._get_html_body(msg)
        if html_text:
            return self._extract_text_from_html(html_text)
        
        return plain_text or ''
    
    def _get_plain_text_body(self, msg):
        """Extrae el cuerpo de texto plano del email"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        return part.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        continue
        else:
            if msg.get_content_type() == 'text/plain':
                try:
                    return msg.get_payload(decode=True).decode(errors='ignore')
                except Exception:
                    pass
        return ''
    
    def _get_html_body(self, msg):
        """Extrae el cuerpo HTML del email"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    try:
                        return part.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        continue
        else:
            if msg.get_content_type() == 'text/html':
                try:
                    return msg.get_payload(decode=True).decode(errors='ignore')
                except Exception:
                    pass
        return ''
    
    def _extract_text_from_html(self, html_content):
        """Extrae información relevante del HTML bancario"""
        import re
        
        # Limpiar HTML básico
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Buscar patrones específicos de emails bancarios
        relevant_info = []
        
        # Patrones de búsqueda para información bancaria
        patterns = {
            'titulo': r'(Comprobante de [^\.]+|Transferencia a [^\.]+|Cargo en [^\.]+|Compra con [^\.]+)',
            'monto': r'\$\s*[\d,\.]+',
            'destinatario': r'(?:Nombre y Apellido|Destinatario)[:\s]*([A-Za-z\s]+)',
            'comercio': r'(?:Comercio|Establecimiento)[:\s]*([A-Za-z0-9\s\-]+)',
            'fecha_hora': r'(?:Fecha y Hora)[:\s]*([^\.]+)',
            'transaccion': r'(?:Transacción)[:\s]*([A-Z0-9]+)',
            'cuenta_origen': r'(?:N°? de Cuenta)[:\s]*([0-9\-]+)',
            'tipo_cuenta': r'(?:Tipo de Cuenta)[:\s]*([A-Za-z\s]+)',
            'banco': r'(?:Banco)[:\s]*([A-Za-z\s/]+)',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Limpiar y agregar matches
                clean_matches = [m.strip() for m in matches if m.strip()]
                if clean_matches:
                    relevant_info.append(f"{key.replace('_', ' ')}: {', '.join(clean_matches[:3])}")  # Máximo 3 matches
        
        # Extraer secciones importantes
        sections = ['Origen', 'Destino', 'Monto', 'Mensaje']
        for section in sections:
            # Buscar contenido entre sección y próxima sección o final
            pattern = rf'{section}.*?(?={"|".join(sections)}|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(0).strip()
                # Limpiar y resumir
                section_text = re.sub(r'\s+', ' ', section_text)
                if len(section_text) > 20:  # Solo si tiene contenido útil
                    relevant_info.append(section_text[:200])  # Limitar a 200 chars
        
        # Combinar información relevante
        if relevant_info:
            result = '\n'.join(relevant_info)
            # Limitar tamaño total para el LLM
            return result[:2000] if len(result) > 2000 else result
        
        # Fallback: devolver texto limpio pero limitado
        return text[:1500] if len(text) > 1500 else text
    
    def _build_imap_search(self):
        """Construye la query de búsqueda IMAP"""
        search_parts = []
        
        # Filtro por fecha
        cutoff = self._ensure_utc(self.account.last_checked)
        if cutoff:
            date_str = cutoff.strftime("%d-%b-%Y")
            search_parts.extend(["SINCE", date_str])
        
        # Filtro por remitentes
        allowed_senders = [s for s in Config.ALLOWED_BANK_SENDERS if s]
        if allowed_senders:
            from_parts = []
            for sender in allowed_senders:
                from_parts.extend(["FROM", sender])
            
            # Construir OR para múltiples remitentes
            if len(allowed_senders) > 1:
                or_parts = ["OR"]
                or_parts.extend(from_parts)
                search_parts = or_parts + search_parts if search_parts else or_parts
            else:
                search_parts = from_parts + search_parts
        
        return '(' + ' '.join(search_parts) + ')' if search_parts else '(UNSEEN)'
    
    def _parse_email_date(self, msg):
        """Extrae y normaliza la fecha del email"""
        date_hdr = msg.get('Date')
        if not date_hdr:
            return None
        
        try:
            msg_dt = email.utils.parsedate_to_datetime(date_hdr)
            return self._ensure_utc(msg_dt)
        except Exception:
            return None
    
    def _is_from_bank(self, email_from):
        """Verifica si el email viene de un banco permitido"""
        from_lower = email_from.lower()
        return any(sender in from_lower for sender in Config.ALLOWED_BANK_SENDERS)
    
    def _create_email_data(self, msg, parsed_data):
        """Crea estructura de datos del email procesado"""
        msg_dt = self._parse_email_date(msg)
        msg_id = msg.get('Message-ID') or f"{self.account.id}:{id(msg)}"
        
        # Usar fecha del email o fecha parseada por LLM
        date_val = msg_dt or datetime.now(timezone.utc)
        if parsed_data.get('fecha_iso'):
            try:
                date_val = datetime.fromisoformat(parsed_data['fecha_iso'])
                date_val = self._ensure_utc(date_val)
            except Exception:
                pass
        
        return {
            'email_id': msg_id,
            'date': date_val,
            'amount': parsed_data.get('monto', 0.0),
            'merchant': parsed_data.get('comercio'),
            'type': parsed_data.get('tipo_transaccion', 'desconocido'),
            'suggested_category': parsed_data.get('posible_categoria', 'otros'),
            'email_date': msg_dt
        }
    
    def process_emails(self):
        """Procesa todos los emails nuevos de la cuenta"""
        current_app.logger.debug('Procesando cuenta %s (last_checked=%s)', 
                                self.account.id, self.account.last_checked)
        
        conn = imaplib.IMAP4_SSL(self.account.imap_host, Config.IMAP_PORT)
        new_transactions = []
        max_date_seen = self._ensure_utc(self.account.last_checked)
        
        try:
            conn.login(self.imap_user, self.imap_password)
            conn.select(Config.IMAP_FOLDER)
            
            # Buscar emails
            criteria = self._build_imap_search()
            current_app.logger.debug('Búsqueda IMAP: %s', criteria)
            
            status, data = conn.search(None, criteria)
            if status != 'OK':
                current_app.logger.error('Falló búsqueda IMAP para cuenta %s', self.account.id)
                return []
            
            email_ids = data[0].split()
            current_app.logger.debug('Encontrados %d emails', len(email_ids))
            
            for email_id in email_ids:
                try:
                    email_data = self._process_single_email(conn, email_id)
                    if email_data:
                        new_transactions.append(email_data)
                        if email_data['email_date']:
                            if max_date_seen is None or email_data['email_date'] > max_date_seen:
                                max_date_seen = email_data['email_date']
                except Exception as e:
                    current_app.logger.error('Error procesando email %s: %s', email_id, e)
            
            # Actualizar fecha de última revisión
            if max_date_seen:
                DatabaseManager.update_last_checked(self.account, max_date_seen)
            
            return new_transactions
            
        finally:
            try:
                conn.logout()
            except Exception:
                pass
    
    def _process_single_email(self, conn, email_id):
        """Procesa un email individual"""
        status, msg_data = conn.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None
        
        raw_msg = msg_data[0][1]
        msg = email.message_from_bytes(raw_msg)
        # Verificar si es de un banco
        from_header = self._decode_header(msg.get('From', ''))
        if not self._is_from_bank(from_header):
            return None
        
        # Verificar duplicados
        msg_id = msg.get('Message-ID') or f"{self.account.id}:{email_id.decode()}"
        if DatabaseManager.is_duplicate_transaction(msg_id):
            current_app.logger.debug('Email duplicado: %s', msg_id)
            return None
        
        # Parsear con LLM
        subject = self._decode_header(msg.get('Subject', ''))
        body = self._get_email_body(msg)

        if self.is_subject_supported(subject):
            current_app.logger.debug('Procesando email con asunto: %s', subject)
            current_app.logger.debug('Body extraído (primeros 500 chars): %s', body[:500])
            parsed_data = parse_email(subject, body)
            current_app.logger.debug('Datos parseados: %s', parsed_data)
            return self._create_email_data(msg, parsed_data)
        else:
            current_app.logger.debug('Asunto no soportado: %s', subject)
            return None


def poll_once(app):
    """Ejecuta un ciclo de polling para todas las cuentas"""
    with app.app_context():
        accounts = DatabaseManager.get_enabled_accounts()
        if not accounts:
            current_app.logger.warning('No hay cuentas habilitadas')
            return []
        
        all_new_transactions = []
        
        for account in accounts:
            try:
                processor = EmailProcessor(account)
                new_emails = processor.process_emails()
                
                for email_data in new_emails:
                    # Obtener usuario para notificación
                    user = DatabaseManager.get_user_for_account(account)
                    if not user:
                        current_app.logger.warning('Cuenta %s sin usuarios', account.id)
                        continue
                    
                    # Crear transacción pendiente
                    tx = DatabaseManager.create_pending_transaction(email_data, user)
                    all_new_transactions.append(tx)
                    
                    # Notificar por Telegram para que el usuario describa la transacción
                    notify_new_transaction(app, tx)
                
                current_app.logger.info('Cuenta %s: %d nuevas transacciones', 
                                      account.id, len(new_emails))
                
            except Exception as e:
                current_app.logger.exception('Error procesando cuenta %s: %s', account.id, e)
        
        return all_new_transactions


def run_poller(app):
    """Loop principal del poller"""
    with app.app_context():
        app.logger.info('Iniciando email poller (intervalo %ss)', Config.POLL_INTERVAL)
    
    while True:
        try:
            new_transactions = poll_once(app)
            if new_transactions:
                with app.app_context():
                    current_app.logger.info('Total nuevas transacciones: %d', len(new_transactions))
            time.sleep(Config.POLL_INTERVAL)
        except Exception as e:
            with app.app_context():
                current_app.logger.exception('Error en poller: %s', e)
            time.sleep(Config.POLL_INTERVAL)
