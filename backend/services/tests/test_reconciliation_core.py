from decimal import Decimal
from services.reconciliation_core import select_settled, distribute_clp


def test_select_settled_exacto():
    # 100 + 230 = 330 -> cubre 2
    assert select_settled([Decimal('100'), Decimal('230'), Decimal('50')], Decimal('330')) == 2


def test_select_settled_se_detiene_al_cubrir():
    assert select_settled([Decimal('200'), Decimal('200')], Decimal('330')) == 2
    assert select_settled([Decimal('400')], Decimal('330')) == 1


def test_distribute_suma_exacta():
    out = distribute_clp([Decimal('100'), Decimal('230')], Decimal('299185'))
    assert sum(out) == Decimal('299185')
    assert len(out) == 2
    # proporcional: el primero ~ 100/330
    assert out[0] == (Decimal('299185') * Decimal('100') / Decimal('330')).quantize(Decimal('0.01'))
