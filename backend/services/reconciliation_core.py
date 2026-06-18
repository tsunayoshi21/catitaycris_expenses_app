from decimal import Decimal


def select_settled(amounts: list[Decimal], usd_paid: Decimal) -> int:
    acc = Decimal('0')
    count = 0
    for a in amounts:
        if acc >= usd_paid:
            break
        acc += a
        count += 1
    return count


def distribute_clp(amounts: list[Decimal], clp_total: Decimal) -> list[Decimal]:
    total = sum(amounts, Decimal('0'))
    if total <= 0:
        return [Decimal('0.00') for _ in amounts]
    out = [(clp_total * a / total).quantize(Decimal('0.01')) for a in amounts]
    # ajustar el redondeo en el ultimo para cuadrar exacto
    out[-1] += clp_total - sum(out, Decimal('0'))
    return out
