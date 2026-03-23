from django.db import models
from django.db.models import Sum


TRANSACTION_TYPE_CHOICES = [
    ('debito', 'Débito'),
    ('credito', 'Crédito'),
    ('transferencia', 'Transferencia'),
    ('ingreso', 'Ingreso'),
    ('desconocido', 'Desconocido'),
]


class Category(models.Model):
    name = models.CharField(max_length=100)  # slugified
    label = models.CharField(max_length=200)  # display name
    is_default = models.BooleanField(default=False)
    owner = models.ForeignKey(
        'users.CustomUser',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('name', 'owner')]
        indexes = [
            models.Index(fields=['owner', 'is_default']),
        ]

    def __str__(self):
        return self.label


class Person(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='persons')
    name = models.CharField(max_length=200)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'name')]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField(db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    merchant = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='desconocido')
    description = models.TextField(null=True, blank=True)
    category_name = models.CharField(max_length=100, null=True, blank=True)
    category = models.ForeignKey(
        Category,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions'
    )
    raw_email_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['type']),
            models.Index(fields=['category_name']),
        ]

    @property
    def net_amount(self):
        paid_back = self.splits.filter(paid_back=True).aggregate(total=Sum('amount'))['total'] or 0
        return self.amount - paid_back

    def __str__(self):
        return f"{self.date:%Y-%m-%d} {self.merchant or ''} ${self.amount}"


class ExpenseSplit(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='splits')
    person = models.ForeignKey(
        Person,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='splits'
    )
    person_name_snapshot = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_back = models.BooleanField(default=False)
    paid_back_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['transaction', 'paid_back']),
        ]


class TelegramNotification(models.Model):
    """Outbox pattern -- replaces in-memory Queue, survives container restarts."""
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sent']),
        ]
