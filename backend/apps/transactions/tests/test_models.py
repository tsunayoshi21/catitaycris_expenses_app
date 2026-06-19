# backend/apps/transactions/tests/test_models.py
from decimal import Decimal
import pytest
from apps.transactions.models import Transaction, SETTLEMENT_TYPES
from apps.users.models import CustomUser


@pytest.fixture
def user(db):
    return CustomUser.objects.create(username='u1')


@pytest.mark.django_db
def test_defaults(user):
    tx = Transaction.objects.create(user=user, date='2026-01-01T00:00:00Z', amount=Decimal('1000'))
    assert tx.currency == 'CLP'
    assert tx.fx_status == 'na'
    assert tx.settled_by is None


@pytest.mark.django_db
def test_net_amount_uses_amount_clp(user):
    tx = Transaction.objects.create(
        user=user, date='2026-01-01T00:00:00Z', amount=Decimal('5'),
        currency='USD', amount_clp=Decimal('4500'),
    )
    assert tx.net_amount == Decimal('4500')


def test_settlement_types_constant():
    assert 'pago_tarjeta' in SETTLEMENT_TYPES
    assert 'credito' not in SETTLEMENT_TYPES
