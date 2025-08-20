from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import Transaction, User
from .services.database import db
import logging
from datetime import datetime, date, time, timedelta, timezone
from urllib.parse import urlparse, urljoin

# Logger para este módulo
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


def _is_safe_url(target):
    try:
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    except Exception:
        return False


@bp.route('/')
@login_required
def index():
    return render_template('dashboard.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()  # previene fijación de sesión
            login_user(user)
            next_url = request.args.get('next')
            if next_url and _is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('main.index'))
        flash('Credenciales inválidas', 'danger')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@bp.route('/transactions')
@login_required
def transactions_page():
    return render_template('transactions.html')


def _parse_date_filters(args):
    """Devuelve (start_utc, end_utc) o (None, None) según filtros year/month/week/day."""
    try:
        day_str = args.get('day')
        year = args.get('year', type=int)
        month = args.get('month', type=int)
        week = args.get('week', type=int)

        if day_str:
            d = datetime.fromisoformat(day_str).date()
            start = datetime.combine(d, time.min, tzinfo=timezone.utc)
            end = start + timedelta(days=1)
            return start, end
        if year and week:
            # ISO week (Mon-Sun)
            d = date.fromisocalendar(year, week, 1)
            start = datetime.combine(d, time.min, tzinfo=timezone.utc)
            end = start + timedelta(days=7)
            return start, end
        if year and month:
            d = date(year, month, 1)
            if month == 12:
                d2 = date(year + 1, 1, 1)
            else:
                d2 = date(year, month + 1, 1)
            start = datetime.combine(d, time.min, tzinfo=timezone.utc)
            end = datetime.combine(d2, time.min, tzinfo=timezone.utc)
            return start, end
        if year:
            start = datetime(year, 1, 1, tzinfo=timezone.utc)
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            return start, end
        return None, None
    except Exception as e:
        logger.debug('Error parseando filtros de fecha: %s', e)
        return None, None


@bp.route('/api/transactions')
@login_required
def api_transactions():
    # Filtros
    q = (request.args.get('q') or '').strip().lower()
    category = (request.args.get('category') or '').strip().lower()
    ttype = request.args.get('type')

    start, end = _parse_date_filters(request.args)

    query = Transaction.query.filter_by(user_id=current_user.id)
    logger.info(f"Transacciones de usuario {current_user.id} - Filtros: q={q}, category={category}, type={ttype}, start={start}, end={end}")
    

    if start and end:
        query = query.filter(Transaction.date >= start, Transaction.date < end)
    if category:
        query = query.filter(db.func.lower(Transaction.category).contains(category))
    if ttype:
        query = query.filter(Transaction.type == ttype)

    txs = query.order_by(Transaction.date.desc()).limit(2000).all()

    if q:
        def match_q(t: Transaction) -> bool:
            blob = f"{t.merchant or ''} {t.description or ''} {t.category or ''} {t.type or ''}".lower()
            return q in blob
        txs = [t for t in txs if match_q(t)]

    return jsonify([t.to_dict() for t in txs])


@bp.route('/api/update_transaction', methods=['POST'])
@login_required
def api_update_transaction():
    data = request.get_json(force=True)
    tx_id = data.get('id')
    if not tx_id:
        return jsonify({'ok': False, 'error': 'id requerido'}), 400

    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()
    if not tx:
        return jsonify({'ok': False, 'error': 'no encontrado'}), 404

    # Campos editables
    if 'description' in data:
        tx.description = (data['description'] or '').strip() or None
    if 'category' in data:
        tx.category = (data['category'] or '').strip() or None

    db.session.commit()
    return jsonify({'ok': True, 'transaction': tx.to_dict()})
