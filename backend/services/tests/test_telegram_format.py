"""Pure unit tests for format_amount — no DB, no Django setup needed."""
from decimal import Decimal

import pytest


def get_format_amount():
    """Import format_amount without triggering heavy telegram/Django imports."""
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(__file__), '..', 'telegram_bot.py')
    spec = importlib.util.spec_from_file_location('telegram_bot', os.path.abspath(path))
    # We only need the pure helper; patch the heavy imports away before loading
    import unittest.mock as mock
    with mock.patch.dict('sys.modules', {
        'telegram': mock.MagicMock(),
        'telegram.ext': mock.MagicMock(),
        'asgiref': mock.MagicMock(),
        'asgiref.sync': mock.MagicMock(),
        'django': mock.MagicMock(),
        'django.conf': mock.MagicMock(),
        'django.db': mock.MagicMock(),
        'django.utils': mock.MagicMock(),
        'django.utils.timezone': mock.MagicMock(),
        'apps': mock.MagicMock(),
        'apps.accounts': mock.MagicMock(),
        'apps.accounts.models': mock.MagicMock(),
        'apps.transactions': mock.MagicMock(),
        'apps.transactions.models': mock.MagicMock(),
        'apps.users': mock.MagicMock(),
        'apps.users.models': mock.MagicMock(),
        'services': mock.MagicMock(),
        'services.llm': mock.MagicMock(),
    }):
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod.format_amount


format_amount = get_format_amount()


def test_usd_estimated_with_clp():
    result = format_amount('USD', Decimal('2.26'), Decimal('2034'), 'estimated')
    assert result == 'US$2.26 (≈ $2,034 CLP)'


def test_usd_final_with_clp():
    result = format_amount('USD', Decimal('330.00'), Decimal('299185'), 'final')
    assert result == 'US$330.00 ($299,185 CLP)'


def test_usd_no_clp():
    result = format_amount('USD', Decimal('5.00'), None, 'estimated')
    assert result == 'US$5.00'


def test_clp():
    result = format_amount('CLP', Decimal('103500'), Decimal('103500'), 'na')
    assert result == '$103,500 CLP'
