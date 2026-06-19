from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from apps.users.models import CustomUser
from apps.transactions.models import Transaction


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(username='pag', password='x')


def _make_transactions(user, n):
    for i in range(n):
        Transaction.objects.create(
            user=user,
            date=f'2026-05-{(i % 28) + 1:02d}T10:00:00Z',
            amount=Decimal('1000'),
            amount_clp=Decimal('1000'),
            type='credito',
            currency='CLP',
            merchant=f'comercio-{i}',
        )


@pytest.mark.django_db
def test_page_size_query_param_es_respetado(user):
    _make_transactions(user, 30)
    client = APIClient(); client.force_authenticate(user)

    resp = client.get('/api/transactions/?page=1&page_size=25')
    assert resp.status_code == 200
    data = resp.json()
    assert data['count'] == 30          # total real, no la página
    assert len(data['results']) == 25   # respeta el page_size pedido
    assert data['next'] is not None     # hay una segunda página

    resp2 = client.get('/api/transactions/?page=2&page_size=25')
    assert len(resp2.json()['results']) == 5


@pytest.mark.django_db
def test_busqueda_abarca_todas_las_filas_no_solo_la_pagina(user):
    # 30 transacciones genéricas + 1 que coincide con la búsqueda, fuera de la 1ª página.
    _make_transactions(user, 30)
    Transaction.objects.create(
        user=user, date='2026-05-01T09:00:00Z', amount=Decimal('1000'),
        amount_clp=Decimal('1000'), type='credito', currency='CLP',
        merchant='UNICORNIO',
    )
    client = APIClient(); client.force_authenticate(user)

    # Aunque pidamos una página pequeña, la búsqueda filtra sobre todo el dataset.
    resp = client.get('/api/transactions/?page=1&page_size=10&search=UNICORNIO')
    assert resp.status_code == 200
    data = resp.json()
    assert data['count'] == 1
    assert len(data['results']) == 1
    assert data['results'][0]['merchant'] == 'UNICORNIO'
