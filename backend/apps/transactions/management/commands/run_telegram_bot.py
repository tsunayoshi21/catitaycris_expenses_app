import asyncio
import logging

from django.core.management.base import BaseCommand

from services.telegram_bot import build_and_run_bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the Telegram bot daemon'

    def handle(self, *args, **options):
        logger.info('Iniciando Telegram bot como management command...')
        asyncio.run(build_and_run_bot())
