import asyncio
import logging

from django.core.management.base import BaseCommand

from services.email_poller import run_poller

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the email poller daemon'

    def handle(self, *args, **options):
        logger.info('Iniciando email poller como management command...')
        asyncio.run(run_poller())
