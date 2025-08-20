import os
from flask import Flask, jsonify, redirect, url_for, request, send_from_directory
from flask_login import LoginManager
from app.config import Config
from app.services.database import db
from app.models import User
from app.routes import bp
from app.services.telegram_bot import build_and_run_bot
from app.services.email_poller import run_poller
import threading
import logging

# Integraciones de seguridad

from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
_has_security_libs = True

# Inicializar logging lo antes posible
Config.configure_logging()

# Logger para este módulo
logger = logging.getLogger(__name__)


login_manager = LoginManager()
login_manager.login_view = 'main.login'


csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

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
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'app', 'static'),
        static_url_path='/static'
    )
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
            return dict(csrf_token=generate_csrf)

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
            return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/x-icon')
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



app = create_app()

if __name__ == '__main__':
    # Ejecutar servidor de desarrollo
    app.run(host='0.0.0.0', port=5000, debug=True)
