# Generated by Django 2.2.10 on 2022-08-01 06:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0122_auto_20220801_1224'),
        ('payments', '0003_admissionguidanceformorder_admissionguidanceformtransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolTransferDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transfer_id', models.CharField(blank=True, max_length=100, null=True)),
                ('recipient', models.CharField(blank=True, max_length=100, null=True)),
                ('amount', models.FloatField(blank=True, default=0, null=True)),
                ('notes', models.TextField(blank=True, max_length=100, null=True)),
                ('payment_done_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='school_transfer_detail', to='schools.SchoolProfile')),
            ],
        ),
        migrations.CreateModel(
            name='SchoolSettlementAccounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razorpay_account_id', models.CharField(blank=True, max_length=120, null=True)),
                ('school', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='settelment_accounts', to='schools.SchoolProfile')),
            ],
        ),
    ]