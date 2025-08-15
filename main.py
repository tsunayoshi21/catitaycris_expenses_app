import threading
from flask import Flask
from app.config import Config
from app.database import db
from app.models import Account, User, Transaction
from app.routes import bp
from app.telegram_bot import build_and_run_bot, notify_new_transaction
from app.email_poller import run_poller
import os
import logging
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    level_name = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    level = getattr(logging, level_name, logging.DEBUG)
    app.logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    # Evitar duplicados si se recarga
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        file_handler = RotatingFileHandler('finanzas_app.log', maxBytes=1_000_000, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        app.logger.addHandler(file_handler)
    # Stream handler (stdout)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(level)
        app.logger.addHandler(sh)


def create_app(start_services: bool = True):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'))
    configure_logging(app)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        # Si no hay cuenta, el admin deberá crearla manualmente por ahora.
    # Lanzar bot
    if start_services:
        build_and_run_bot(app)
        # Lanzar poller
        t = threading.Thread(target=run_poller, args=(app,), daemon=True)
        t.start()
    app.logger.info('Aplicación iniciada (services=%s)', start_services)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
