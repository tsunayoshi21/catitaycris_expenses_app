from decimal import Decimal
import pytest
from apps.transactions.models import Transaction
from apps.users.models import CustomUser
from services.reconciliation import (
    reconcile_national_payment, reconcile_international_payment,
)


@pytest.fixture
def user(db):
    return CustomUser.objects.create(username='u1')


def _credito(user, amount, currency='CLP', fx_status='na', amount_clp=None, date='2026-01-05T10:00:00Z'):
    return Transaction.objects.create(
        user=user, date=date, amount=Decimal(amount), currency=currency,
        type='credito', fx_status=fx_status,
        amount_clp=Decimal(amount_clp) if amount_clp is not None else (Decimal(amount) if currency == 'CLP' else None),
    )


@pytest.mark.django_db
def test_national_crea_comision_residual(user):
    _credito(user, '70000')
    _credito(user, '8000')
    pago = Transaction.objects.create(
        user=user, date='2026-01-28T22:39:00Z', amount=Decimal('82171'),
        amount_clp=Decimal('82171'), type='pago_tarjeta',
    )
    reconcile_national_payment(pago)
    comision = Transaction.objects.get(type='comision')
    assert comision.amount_clp == Decimal('4171')  # 82171 - 78000
    assert Transaction.objects.filter(type='credito', settled_by=pago).count() == 2


@pytest.mark.django_db
def test_national_sin_compras_es_pura_comision(user):
    pago = Transaction.objects.create(
        user=user, date='2026-01-28T22:39:00Z', amount=Decimal('4700'),
        amount_clp=Decimal('4700'), type='pago_tarjeta',
    )
    reconcile_national_payment(pago)
    assert Transaction.objects.get(type='comision').amount_clp == Decimal('4700')


@pytest.mark.django_db
def test_international_finaliza_y_cuadra(user):
    c1 = _credito(user, '100', currency='USD', fx_status='estimated', date='2026-05-01T10:00:00Z')
    c2 = _credito(user, '230', currency='USD', fx_status='estimated', date='2026-05-02T10:00:00Z')
    pago = Transaction.objects.create(
        user=user, date='2026-05-28T22:39:00Z', amount=Decimal('330'),
        currency='USD', amount_clp=Decimal('299185'), type='pago_tarjeta',
    )
    reconcile_international_payment(pago, Decimal('330'), Decimal('299185'))
    c1.refresh_from_db(); c2.refresh_from_db()
    assert c1.fx_status == 'final' and c2.fx_status == 'final'
    assert c1.amount_clp + c2.amount_clp == Decimal('299185')
    assert c1.settled_by == pago


@pytest.mark.django_db
def test_idempotente(user):
    _credito(user, '78000')
    pago = Transaction.objects.create(
        user=user, date='2026-01-28T22:39:00Z', amount=Decimal('82171'),
        amount_clp=Decimal('82171'), type='pago_tarjeta',
    )
    reconcile_national_payment(pago)
    reconcile_national_payment(pago)  # segunda vez no debe duplicar
    assert Transaction.objects.filter(type='comision').count() == 1
