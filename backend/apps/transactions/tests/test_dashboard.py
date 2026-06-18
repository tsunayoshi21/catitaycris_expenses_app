from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from apps.users.models import CustomUser
from apps.transactions.models import Transaction


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(username='u1', password='x')


@pytest.mark.django_db
def test_dashboard_excluye_pago_y_marca_estimados(user):
    Transaction.objects.create(user=user, date='2026-05-10T10:00:00Z', amount=Decimal('100000'),
                               amount_clp=Decimal('100000'), type='credito', currency='CLP')
    Transaction.objects.create(user=user, date='2026-05-12T10:00:00Z', amount=Decimal('5'),
                               amount_clp=Decimal('4500'), type='credito', currency='USD', fx_status='estimated')
    Transaction.objects.create(user=user, date='2026-05-28T10:00:00Z', amount=Decimal('82171'),
                               amount_clp=Decimal('82171'), type='pago_tarjeta', currency='CLP')
    client = APIClient(); client.force_authenticate(user)
    resp = client.get('/api/dashboard/?year=2026&month=5')
    assert resp.status_code == 200
    data = resp.json()
    total = sum(Decimal(m['total']) for m in data['monthly_totals'])
    assert total == Decimal('104500')  # excluye el pago de 82171
    assert data['has_estimates'] is True
