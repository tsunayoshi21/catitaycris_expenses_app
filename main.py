import threading
from flask import Flask, jsonify, redirect, url_for, request, send_from_directory, session
from flask_login import LoginManager
from app.config import Config
from app.services.database import db
from app.models import Account, User, Transaction
from app.routes import bp
from app.services.telegram_bot import build_and_run_bot, notify_new_transaction
from app.services.email_poller import run_poller
import os
import logging
from logging.handlers import RotatingFileHandler

# Logger para este módulo
logger = logging.getLogger(__name__)


class AppOnlyFilter(logging.Filter):
    """Filtro que solo permite logs de nuestros módulos de la aplicación"""
    def filter(self, record):
        # Solo permitir logs que empiecen con 'app.' o '__main__'
        return (record.name.startswith('app.') or 
                record.name == '__main__' or
                record.name.startswith('__main__'))


def configure_global_logging():
    """Configura el logging global para toda la aplicación"""
    level_name = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    level = getattr(logging, level_name, logging.INFO)
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturar todo, pero filtraremos
    
    # Evitar duplicados
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    # File handler - solo logs de nuestra app
    file_handler = RotatingFileHandler('finanzas_app.log', maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    file_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(file_handler)
    
    # Stream handler (stdout) - solo logs de nuestra app
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    stream_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(stream_handler)
    
    # Configurar loggers específicos para nuestros módulos
    app_loggers = [
        '__main__',
        'app.services.email_poller',
        'app.services.telegram_bot', 
        'app.services.database',
        'app.services.llm',
        'app.routes',
        'app.models'
    ]
    
    for logger_name in app_loggers:
        app_logger = logging.getLogger(logger_name)
        app_logger.setLevel(level)
        # No agregar handlers aquí, heredarán del root
    
    # Silenciar loggers ruidosos de librerías externas
    noisy_loggers = [
        'httpcore',
        'httpx', 
        'telegram',
        'telegram.ext',
        'urllib3',
        'requests',
        'asyncio',
        'werkzeug'
    ]
    
    for logger_name in noisy_loggers:
        noisy_logger = logging.getLogger(logger_name)
        noisy_logger.setLevel(logging.ERROR)  # Solo errores críticos
    
    logger.info("Logging configurado - nivel: %s, filtrado solo app", level_name)


login_manager = LoginManager()
login_manager.login_view = 'main.login'

# Integraciones de seguridad
try:
    from flask_wtf.csrf import CSRFProtect, generate_csrf
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    _has_security_libs = True
except Exception:
    CSRFProtect = None
    Limiter = None
    get_remote_address = None
    generate_csrf = None
    _has_security_libs = False

csrf = CSRFProtect() if CSRFProtect else None
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://") if Limiter else None

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

@login_manager.unauthorized_handler
def unauthorized():
    # Responder JSON para endpoints API
    if request.path.startswith('/api/'):
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    return redirect(url_for('main.login'))


def create_app(start_services: bool = True):
    # Configurar logging global antes de crear la app
    configure_global_logging()
    
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'))
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # CSRF
    if csrf:
        csrf.init_app(app)
        @app.context_processor
        def inject_csrf_token():
            # Permite usar {{ csrf_token() }} en templates
            return dict(csrf_token=(generate_csrf if generate_csrf else (lambda: ''))) 

    # Registrar blueprints primero para que existan endpoints
    app.register_blueprint(bp)

    # Eximir endpoints API de CSRF (llamados via fetch)
    if csrf:
        for endpoint, view in app.view_functions.items():
            if endpoint.startswith('main.api_'):
                csrf.exempt(view)

    # Rate limiting básico (después de registrar blueprint)
    if limiter:
        limiter.init_app(app)
        if 'main.login' in app.view_functions:
            limiter.limit("5/minute;20/hour")(app.view_functions['main.login'])

    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon to avoid 404s"""
        try:
            return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/x-icon')
        except Exception:
            # Fallback: 204 No Content to avoid log noise if file missing
            from flask import Response
            return Response(status=204)

    with app.app_context():
        db.create_all()
        # Si no hay cuenta, el admin deberá crearla manualmente por ahora.
    
    # Lanzar bot y poller
    if start_services:
        build_and_run_bot(app)
        t = threading.Thread(target=run_poller, args=(app,), daemon=True)
        t.start()
    
    logger.info('Aplicación iniciada (services=%s)', start_services)
    return app



if __name__ == '__main__':
    app = create_app()

    app.run(host='0.0.0.0', port=5000)
