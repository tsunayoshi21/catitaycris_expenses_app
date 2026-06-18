from decimal import Decimal
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
from apps.users.models import CustomUser
from apps.transactions.models import Transaction, Category


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(username='u_ser', password='x')


# ---------------------------------------------------------------------------
# Fix 1: TransactionListSerializer must expose currency / amount_clp / fx_status
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_transaction_list_exposes_currency_fields(user):
    """LIST endpoint must return currency, amount_clp, fx_status for each item."""
    Transaction.objects.create(
        user=user,
        date='2026-06-01T12:00:00Z',
        amount=Decimal('2.26'),
        amount_clp=Decimal('2034.00'),
        type='credito',
        currency='USD',
        fx_status='estimated',
    )
    client = APIClient()
    client.force_authenticate(user)
    resp = client.get('/api/transactions/')
    assert resp.status_code == 200
    items = resp.json()['results'] if 'results' in resp.json() else resp.json()
    assert len(items) == 1
    item = items[0]
    assert item['currency'] == 'USD'
    assert Decimal(item['amount_clp']) == Decimal('2034.00')
    assert item['fx_status'] == 'estimated'


# ---------------------------------------------------------------------------
# Fix 2: load_default_categories seeds a 'comisiones' category
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_load_default_categories_seeds_comisiones():
    """After running the seed command a default 'comisiones' category must exist."""
    call_command('load_default_categories', verbosity=0)
    assert Category.objects.filter(name='comisiones', is_default=True, owner=None).exists()
