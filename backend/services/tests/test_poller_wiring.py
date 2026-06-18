from decimal import Decimal
from services.email_poller import build_purchase_fields


def test_compra_clp():
    f = build_purchase_fields({'tipo_transaccion': 'credito', 'monto': 103500.0, 'moneda': 'CLP'}, None)
    assert f['currency'] == 'CLP'
    assert f['amount_clp'] == Decimal('103500')
    assert f['fx_status'] == 'na'


def test_compra_usd_con_tasa():
    f = build_purchase_fields({'tipo_transaccion': 'credito', 'monto': 2.26, 'moneda': 'USD'}, Decimal('900'))
    assert f['currency'] == 'USD'
    assert f['fx_status'] == 'estimated'
    assert f['amount_clp'] == Decimal('2034.00')  # 2.26 * 900


def test_compra_usd_sin_tasa():
    f = build_purchase_fields({'tipo_transaccion': 'credito', 'monto': 2.26, 'moneda': 'USD'}, None)
    assert f['amount_clp'] is None and f['fx_status'] == 'estimated'
