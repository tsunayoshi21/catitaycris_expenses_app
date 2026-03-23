from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    telegram_chat_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
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
