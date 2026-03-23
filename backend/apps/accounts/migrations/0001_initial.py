from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imap_host', models.CharField(max_length=255)),
                ('imap_user_encrypted', models.BinaryField()),
                ('imap_password_encrypted', models.BinaryField()),
                ('enabled', models.BooleanField(default=True)),
                ('last_checked', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'app_label': 'accounts',
            },
        ),
        migrations.CreateModel(
            name='SystemState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polling_paused', models.BooleanField(default=False)),
                ('paused_reason', models.TextField(blank=True)),
                ('paused_at', models.DateTimeField(blank=True, null=True)),
                ('admin_notified', models.BooleanField(default=False)),
            ],
            options={
                'app_label': 'accounts',
            },
        ),
    ]
