"""Backfill Transaction.category FK from category_name for existing rows."""

from django.db import migrations
from django.db.models import Q


def backfill_category_fk(apps, schema_editor):
    Transaction = apps.get_model('transactions', 'Transaction')
    Category = apps.get_model('transactions', 'Category')

    txs = (
        Transaction.objects
        .filter(category__isnull=True, category_name__isnull=False)
        .exclude(category_name='')
        .select_related('user')
    )

    for tx in txs.iterator():
        cat = Category.objects.filter(
            Q(is_default=True) | Q(owner_id=tx.user_id),
            name=tx.category_name,
        ).first()
        if cat:
            Transaction.objects.filter(pk=tx.pk).update(category=cat)


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_telegramnotification_processing_at'),
    ]

    operations = [
        migrations.RunPython(backfill_category_fk, migrations.RunPython.noop),
    ]
