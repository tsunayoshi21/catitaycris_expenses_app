# backend/services/tests/test_fx.py
from decimal import Decimal
import pytest
from services.fx import parse_mindicador, update_estimated_clp
from apps.transactions.models import Transaction
from apps.users.models import CustomUser


def test_parse_mindicador():
    payload = {'serie': [{'fecha': '2026-06-18', 'valor': 906.6}]}
    assert parse_mindicador(payload) == Decimal('906.6')


@pytest.mark.django_db
def test_update_estimated_clp():
    u = CustomUser.objects.create(username='u1')
    tx = Transaction.objects.create(
        user=u, date='2026-06-01T10:00:00Z', amount=Decimal('10'),
        currency='USD', fx_status='estimated', type='credito',
    )
    final = Transaction.objects.create(
        user=u, date='2026-06-01T10:00:00Z', amount=Decimal('10'),
        currency='USD', fx_status='final', amount_clp=Decimal('9000'), type='credito',
    )
    n = update_estimated_clp(Decimal('900'))
    tx.refresh_from_db(); final.refresh_from_db()
    assert n == 1
    assert tx.amount_clp == Decimal('9000.00')
    assert final.amount_clp == Decimal('9000')  # no tocado
