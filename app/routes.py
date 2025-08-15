from flask import Blueprint, jsonify, render_template
from .models import Transaction

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('dashboard.html')

@bp.route('/api/transactions')
def api_transactions():
    txs = Transaction.query.order_by(Transaction.date.desc()).limit(200).all()
    return jsonify([t.to_dict() for t in txs])
