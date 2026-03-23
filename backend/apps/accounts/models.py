import os
from django.db import models
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken


def _get_fernet():
    key = os.environ.get('APP_ENCRYPTION_KEY')
    if not key:
        raise RuntimeError('APP_ENCRYPTION_KEY faltante')
    return Fernet(key.encode() if isinstance(key, str) else key)


class SystemState(models.Model):
    polling_paused = models.BooleanField(default=False)
    paused_reason  = models.TextField(blank=True)
    paused_at      = models.DateTimeField(null=True, blank=True)
    admin_notified = models.BooleanField(default=False)

    class Meta:
        app_label = 'accounts'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Account(models.Model):
    imap_host = models.CharField(max_length=255)
    imap_user_encrypted = models.BinaryField()
    imap_password_encrypted = models.BinaryField()
    enabled = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'

    def set_imap_credentials(self, imap_user: str, imap_password: str):
        f = _get_fernet()
        self.imap_user_encrypted = f.encrypt(imap_user.encode())
        self.imap_password_encrypted = f.encrypt(imap_password.encode())

    def get_imap_credentials(self):
        f = _get_fernet()
        try:
            user = f.decrypt(bytes(self.imap_user_encrypted)).decode()
            pw = f.decrypt(bytes(self.imap_password_encrypted)).decode()
            return user, pw
        except InvalidToken:
            raise RuntimeError('No se pudo descifrar credenciales (clave incorrecta)')
