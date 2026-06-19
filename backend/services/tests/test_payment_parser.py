from decimal import Decimal
from services.payment_parser import parse_national_payment, parse_international_payment, parse_giro

NATIONAL = """Comprobante pago Tarjeta de Crédito Nacional
Origen Tipo de cuenta Cuenta Corriente N° de cuenta 00-442-05758-10
Destino Tipo de tarjeta Tarjeta de Crédito N° de tarjeta ************7636 Utilizado $0
Monto $82.171
Fecha y Hora: jueves 28 de mayo de 2026 22:39"""

INTERNATIONAL = """Comprobante pago Tarjeta de Crédito Internacional
Origen Tipo de cuenta Cuenta Corriente N° de cuenta 00-442-05758-10
Destino Tipo de tarjeta Tarjeta de Crédito N° de tarjeta ************7636 Utilizado USD$0,00
Detalle Monto pagado USD$330,00 Tipo de cambio $907 Monto $299.185"""


def test_national():
    assert parse_national_payment(NATIONAL) == Decimal('82171')


def test_international():
    usd, clp = parse_international_payment(INTERNATIONAL)
    assert usd == Decimal('330.00')
    assert clp == Decimal('299185')


GIRO_5000 = 'Te informamos que se ha realizado un giro en Cajero por $5.000 con cargo a Cuenta ****5810 el 18/10/2025 15:34.'
GIRO_36223 = 'Te informamos que se ha realizado un giro en Cajero por $36.223 con cargo a Cuenta ****5810 el 18/10/2025 15:34.'


def test_giro_5000():
    assert parse_giro(GIRO_5000) == Decimal('5000')


def test_giro_36223():
    assert parse_giro(GIRO_36223) == Decimal('36223')
