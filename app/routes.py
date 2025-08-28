from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from .services.database import DatabaseManager
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
        user = DatabaseManager.get_user_by_username(username)
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
    """Devuelve (start_utc, end_utc) o (None, None) según filtros.

    Soporta dos modos:
    - dateMode=ym: usa year y month (month vacío => todo el año).
    - dateMode=range: usa start y end (YYYY-MM-DD). Si faltan, no filtra.
    """
    try:
        mode = args.get('dateMode', default='range')
        if mode == 'range':
            start_str = args.get('start')
            end_str = args.get('end')
            if not start_str or not end_str:
                return None, None
            d_start = datetime.fromisoformat(start_str).date()
            d_end = datetime.fromisoformat(end_str).date()
            if d_end < d_start:
                d_start, d_end = d_end, d_start
            start = datetime.combine(d_start, time.min, tzinfo=timezone.utc)
            end = datetime.combine(d_end + timedelta(days=1), time.min, tzinfo=timezone.utc)
            return start, end
        else:
            # ym mode
            year = args.get('year', type=int)
            month_raw = args.get('month')
            month = int(month_raw) if (month_raw not in (None, '')) else None
            if not year:
                return None, None
            if month:
                d = date(year, month, 1)
                d2 = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
                start = datetime.combine(d, time.min, tzinfo=timezone.utc)
                end = datetime.combine(d2, time.min, tzinfo=timezone.utc)
                return start, end
            else:
                # Todo el año
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
    # Permitir múltiples 'type' en query: ?type=debito&type=credito
    ttypes = [t for t in request.args.getlist('type') if t]

    start, end = _parse_date_filters(request.args)

    logger.info(
        "Transacciones de usuario %s - Filtros: q=%s, category=%s, types=%s, start=%s, end=%s",
        current_user.id, q, category, ttypes, start, end,
    )

    txs = DatabaseManager.get_transactions_for_user(
        user_id=current_user.id,
        q=q,
        category=category,
        ttypes=ttypes if ttypes else None,
        start=start,
        end=end,
        limit=2000,
    )

    return jsonify([t.to_dict() for t in txs])


@bp.route('/api/update_transaction', methods=['POST'])
@login_required
def api_update_transaction():
    data = request.get_json(force=True)
    tx_id = data.get('id')
    if not tx_id:
        return jsonify({'ok': False, 'error': 'id requerido'}), 400

    description = data.get('description')
    category = data.get('category')

    tx = DatabaseManager.update_transaction_for_user(
        user_id=current_user.id,
        transaction_id=tx_id,
        description=description,
        category=category,
    )

    if not tx:
        return jsonify({'ok': False, 'error': 'no encontrado'}), 404

    return jsonify({'ok': True, 'transaction': tx.to_dict()})
