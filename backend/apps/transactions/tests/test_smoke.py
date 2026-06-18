import pytest


@pytest.mark.django_db
def test_db_available():
    from apps.transactions.models import Transaction
    assert Transaction.objects.count() == 0
