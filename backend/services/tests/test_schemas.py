from services.schemas import ParsedEmail


def test_moneda_default_clp():
    p = ParsedEmail(tipo_transaccion='credito', monto=103500.0)
    assert p.moneda == 'CLP'


def test_moneda_usd():
    p = ParsedEmail(tipo_transaccion='credito', monto=2.26, moneda='USD')
    assert p.moneda == 'USD'
