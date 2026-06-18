from django.core.management.base import BaseCommand
from services.fx import fetch_usd_clp, update_estimated_clp


class Command(BaseCommand):
    help = 'Refresca el tipo de cambio USD/CLP y reestima compras en USD pendientes'

    def handle(self, *args, **options):
        rate = fetch_usd_clp()
        n = update_estimated_clp(rate)
        self.stdout.write(self.style.SUCCESS(f'Tasa {rate}; {n} transacciones reestimadas'))
