import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    telegram_chat_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    telegram_link_token = models.CharField(max_length=12, unique=True, null=True, blank=True)
    telegram_link_token_created_at = models.DateTimeField(null=True, blank=True)
    account = models.ForeignKey(
        'accounts.Account',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='users'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['telegram_chat_id']),
        ]

    def generate_telegram_link_token(self):
        self.telegram_link_token = secrets.token_urlsafe(8)[:10]
        self.telegram_link_token_created_at = timezone.now()
        self.save(update_fields=['telegram_link_token', 'telegram_link_token_created_at'])
        return self.telegram_link_token
