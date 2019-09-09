from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
            ],
            options={
                'verbose_name_plural': 'Campaigns',
                'verbose_name': 'Campaign',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(help_text='Arbitrary voucher value', verbose_name='Value')),
                ('code', models.CharField(blank=True, help_text='Leaving this field empty will generate a random code.', max_length=30, unique=True, verbose_name='Code')),
                ('type', models.CharField(choices=[('monetary', 'Money based voucher'), ('percentage', 'Percentage discount'), ('virtual_currency', 'Virtual currency')], max_length=20, verbose_name='Type')),
                ('user_limit', models.PositiveIntegerField(default=1, verbose_name='User limit')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('valid_until', models.DateTimeField(blank=True, help_text='Leave empty for vouchers that never expire', null=True, verbose_name='Valid until')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='vouchers.Campaign', verbose_name='Campaign')),
            ],
            options={
                'verbose_name_plural': 'Vouchers',
                'verbose_name': 'Voucher',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='VoucherUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('redeemed_at', models.DateTimeField(blank=True, null=True, verbose_name='Redeemed at')),
                ('voucher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='vouchers.Voucher')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='voucheruser',
            unique_together={('voucher', 'user')},
        ),
    ]
