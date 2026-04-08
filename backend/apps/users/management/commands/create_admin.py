import os
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.accounts.models import Account

User = get_user_model()

utc = timezone.utc


class Command(BaseCommand):
    help = 'Crea el usuario admin con is_staff=True usando variables de entorno.'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME')
        password = os.environ.get('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_USERNAME o ADMIN_PASSWORD no están configurados. Saltando.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f'El usuario {username} ya existe. Saltando.'
            ))
            return

        telegram_chat_id = os.environ.get('ADMIN_TELEGRAM_CHAT_ID') or None
        imap_email = os.environ.get('ADMIN_IMAP_EMAIL')
        imap_password = os.environ.get('ADMIN_IMAP_PASSWORD')
        imap_host = os.environ.get('IMAP_HOST', 'imap.gmail.com')

        account = None
        if imap_email and imap_password:
            start_date_str = os.environ.get('ADMIN_IMAP_START_DATE')
            if start_date_str:
                last_checked = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=utc)
            else:
                last_checked = datetime.now(tz=utc)

            account = Account(
                imap_host=imap_host,
                last_checked=last_checked,
            )
            account.set_imap_credentials(imap_email, imap_password)
            account.save()

        user = User.objects.create_user(
            username=username,
            password=password,
            account=account,
            is_staff=True,
            telegram_chat_id=telegram_chat_id,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Usuario {username} creado (id={user.id}, is_staff=True).'
        ))
