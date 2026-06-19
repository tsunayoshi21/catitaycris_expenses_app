import logging
from decimal import Decimal

from apps.transactions.models import Transaction, Category
from .reconciliation_core import select_settled, distribute_clp

logger = logging.getLogger(__name__)


def reconcile_national_payment(payment: Transaction) -> None:
    purchases = list(
        Transaction.objects.filter(
            user=payment.user, type='credito', currency='CLP',
            settled_by__isnull=True, date__lte=payment.date,
        ).order_by('date')
    )
    total = Decimal('0')
    for p in purchases:
        p.settled_by = payment
        p.save(update_fields=['settled_by', 'updated_at'])
        total += p.amount_clp if p.amount_clp is not None else p.amount

    pago_clp = payment.amount_clp if payment.amount_clp is not None else payment.amount
    residual = pago_clp - total
    if residual > Decimal('1'):
        # idempotencia: no recrear si ya existe la comision de este pago
        if not Transaction.objects.filter(type='comision', settled_by=payment).exists():
            cat = Category.get_valid_for_user(payment.user_id).filter(name='comisiones').first()
            Transaction.objects.create(
                user=payment.user, date=payment.date, amount=residual, amount_clp=residual,
                currency='CLP', type='comision', category_name='comisiones', category=cat,
                settled_by=payment, fx_status='na',
            )
    elif residual < 0:
        logger.warning('Pago nacional %s con residual negativo (%s): posible desajuste', payment.id, residual)


def reconcile_international_payment(payment: Transaction, usd_paid: Decimal, clp_total: Decimal) -> None:
    pending = list(
        Transaction.objects.filter(
            user=payment.user, type='credito', currency='USD',
            fx_status='estimated', settled_by__isnull=True,
        ).order_by('date')
    )
    n = select_settled([p.amount for p in pending], usd_paid)
    settled = pending[:n]
    if not settled:
        return
    clps = distribute_clp([p.amount for p in settled], clp_total)
    usd_total = sum((p.amount for p in settled), Decimal('0'))
    rate = (clp_total / usd_total).quantize(Decimal('0.0001'))
    for p, clp in zip(settled, clps):
        p.amount_clp = clp
        p.fx_rate = rate
        p.fx_status = 'final'
        p.settled_by = payment
        p.save(update_fields=['amount_clp', 'fx_rate', 'fx_status', 'settled_by', 'updated_at'])
