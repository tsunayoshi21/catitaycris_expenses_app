from django.db import models
from django.db.models import Q, Sum


TRANSACTION_TYPE_CHOICES = [
    ('debito', 'Débito'),
    ('giro', 'Giro'),
    ('credito', 'Crédito'),
    ('transferencia', 'Transferencia'),
    ('ingreso', 'Ingreso'),
    ('comision', 'Comisión/Cargos'),
    ('pago_tarjeta', 'Pago tarjeta'),
    ('desconocido', 'Desconocido'),
]

CURRENCY_CHOICES = [('CLP', 'CLP'), ('USD', 'USD')]
FX_STATUS_CHOICES = [('na', 'N/A'), ('estimated', 'Estimado'), ('final', 'Final')]

SETTLEMENT_TYPES = frozenset({'pago_tarjeta'})


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

    @staticmethod
    def get_valid_for_user(user_id):
        """Return categories visible to a user: defaults + user-owned."""
        return Category.objects.filter(Q(is_default=True) | Q(owner_id=user_id))


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
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CLP')
    amount_clp = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    fx_status = models.CharField(max_length=10, choices=FX_STATUS_CHOICES, default='na')
    fx_rate = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    settled_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='settles'
    )
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
        base = self.amount_clp if self.amount_clp is not None else self.amount
        paid_back = self.splits.filter(paid_back=True).aggregate(total=Sum('amount'))['total'] or 0
        return base - paid_back

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
    MAX_RETRIES = 5

    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed = models.BooleanField(default=False)
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    processing_at = models.DateTimeField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sent', 'failed']),
        ]
