import re
from decimal import Decimal


def _to_decimal(integer_part: str, decimals: str | None) -> Decimal:
    # "82.171" (puntos = miles) -> 82171 ; decimals separados por coma
    whole = integer_part.replace('.', '')
    return Decimal(f'{whole}.{decimals}') if decimals else Decimal(whole)


def parse_national_payment(body: str) -> Decimal:
    m = re.search(r'Monto\s*\$\s*([\d.]+)(?:,(\d+))?', body, re.IGNORECASE)
    if not m:
        raise ValueError('No se encontro monto en pago nacional')
    return _to_decimal(m.group(1), m.group(2))


def parse_international_payment(body: str) -> tuple[Decimal, Decimal]:
    usd_m = re.search(r'Monto pagado\s*USD\$\s*([\d.]+)(?:,(\d+))?', body, re.IGNORECASE)
    # CLP total: "Monto $..." que NO sea "Monto pagado"
    clp_m = re.search(r'Monto(?!\s*pagado)\s*\$\s*([\d.]+)(?:,(\d+))?', body, re.IGNORECASE)
    if not usd_m or not clp_m:
        raise ValueError('No se pudieron extraer montos del pago internacional')
    return _to_decimal(usd_m.group(1), usd_m.group(2)), _to_decimal(clp_m.group(1), clp_m.group(2))
