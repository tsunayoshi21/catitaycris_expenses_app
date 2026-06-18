import json
import urllib.request
from decimal import Decimal

from apps.transactions.models import Transaction

MINDICADOR_URL = 'https://mindicador.cl/api/dolar'


def parse_mindicador(payload: dict) -> Decimal:
    return Decimal(str(payload['serie'][0]['valor']))


def fetch_usd_clp(url: str = MINDICADOR_URL) -> Decimal:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return parse_mindicador(json.loads(resp.read().decode()))


def update_estimated_clp(rate: Decimal) -> int:
    count = 0
    for tx in Transaction.objects.filter(currency='USD', fx_status='estimated'):
        tx.amount_clp = (tx.amount * rate).quantize(Decimal('0.01'))
        tx.fx_rate = rate
        tx.save(update_fields=['amount_clp', 'fx_rate', 'updated_at'])
        count += 1
    return count
