from django.db import migrations


def backfill(apps, schema_editor):
    Transaction = apps.get_model('transactions', 'Transaction')
    for tx in Transaction.objects.filter(amount_clp__isnull=True):
        tx.amount_clp = tx.amount
        tx.currency = 'CLP'
        tx.fx_status = 'na'
        tx.save(update_fields=['amount_clp', 'currency', 'fx_status'])


class Migration(migrations.Migration):
    dependencies = [('transactions', '0006_transaction_amount_clp_transaction_currency_and_more')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
