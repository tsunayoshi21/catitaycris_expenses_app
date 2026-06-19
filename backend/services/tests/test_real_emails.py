"""Regresión contra cuerpos REALES de correos de Banco de Chile.

Los cuerpos provienen de correos reales extraídos por BeautifulSoup (igual que el
poller en producción), con los datos personales redactados (nombre, N° de cuenta y
N° de tarjeta). Los montos y, sobre todo, la ESTRUCTURA — etiquetas y valores en
líneas separadas, tal como llegan tras el HTML→texto — son reales. Esto bloquea
regresiones que un fixture inventado en una sola línea no detectaría.
"""
from decimal import Decimal

from services.email_poller import classify_subject
from services.payment_parser import (
    parse_national_payment, parse_international_payment, parse_giro,
)

# --- Cuerpos reales sanitizados (etiqueta y valor en líneas separadas) ---

PAGO_NACIONAL = """Banco de Chile | Mi Banco
Comprobante pago Tarjeta de Crédito Nacional
Estimado(a):
NOMBRE APELLIDO
Te informamos que se ha efectuado el pago
                                de la tarjeta de crédito nacional en forma
                                exitosa con el siguiente detalle:
Origen
Tipo de cuenta
Cuenta Corriente
N° de cuenta
00-000-00000-00
Destino
Tipo de tarjeta
Tarjeta de Crédito
N° de tarjeta
************0000
Utilizado
$0
Monto
$82.171
Fecha y Hora:
jueves 28 de mayo de 2026 22:39"""

PAGO_INTERNACIONAL = """Banco de Chile | Mi Banco
Comprobante pago Tarjeta de Crédito Internacional
Estimado(a):
NOMBRE APELLIDO
Te informamos que se ha efectuado el pago
                                de la tarjeta de crédito internacional en forma
                                exitosa con el siguiente detalle:
Origen
Tipo de cuenta
Cuenta Corriente
Nº de cuenta
00-000-00000-00
Destino
Tipo de tarjeta
Tarjeta de Crédito
Nº de tarjeta
************0000
Utilizado
USD$0,00
Detalle
Monto pagado
USD$1,00
Tipo de cambio
$906
Monto
$906
Fecha y Hora:
miércoles 07 de enero de 2026 11:20"""

GIRO = """Banco de Chile
NOMBRE APELLIDO:
Te informamos que se ha realizado un giro en Cajero por $36.223 con cargo a Cuenta ************0000 el 23/05/2026 20:01.
Revisa Saldos y Movimientos en App Mi Banco o Banco en Línea."""

COMPRA_USD = """Banco de Chile
NOMBRE APELLIDO:
Te informamos que se ha realizado una compra por US$151,56 con Tarjeta de Crédito ************0000 en YESSTYLE.COM LIMITED                     el 14/06/2026 16:47."""

COMPRA_CLP = """Banco de Chile
NOMBRE APELLIDO:
Te informamos que se ha realizado una compra por $22.320 con Tarjeta de Crédito ************0000 en KS*Compra RestauJusto    SANTIAGO     CL el 19/05/2026 20:51."""


def test_classify_real_subjects():
    """Los asuntos reales (con tildes) se clasifican correctamente."""
    assert classify_subject('Compra con Tarjeta de Crédito') == 'compra'
    assert classify_subject('Pago de Tarjeta de Crédito Nacional') == 'pago_nacional'
    assert classify_subject('Pago de Tarjeta de Crédito Internacional') == 'pago_internacional'
    assert classify_subject('Giro con Tarjeta de Débito') == 'giro'


def test_parse_real_national_payment():
    # "Monto\n$82.171" multilínea; no debe confundirse con "Utilizado\n$0".
    assert parse_national_payment(PAGO_NACIONAL) == Decimal('82171')


def test_parse_real_international_payment():
    # "Monto pagado\nUSD$1,00" (USD) vs "Monto\n$906" (CLP) — el lookahead los distingue.
    usd, clp = parse_international_payment(PAGO_INTERNACIONAL)
    assert usd == Decimal('1.00')
    assert clp == Decimal('906')


def test_parse_real_giro():
    assert parse_giro(GIRO) == Decimal('36223')


def test_real_purchase_currency_signal():
    """El monto/moneda de las compras los extrae el LLM; aquí verificamos la SEÑAL
    que el prompt usa (US$ -> USD, $ -> CLP) y que el asunto se reconoce."""
    assert 'US$' in COMPRA_USD
    assert 'US$' not in COMPRA_CLP
    assert classify_subject('Compra con Tarjeta de Crédito') == 'compra'
