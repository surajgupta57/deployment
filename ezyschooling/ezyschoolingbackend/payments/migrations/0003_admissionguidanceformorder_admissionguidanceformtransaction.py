# Generated by Django 2.2.10 on 2021-02-20 13:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0026_surveyresponses_taker'),
        ('payments', '0002_admissionguidanceprogrammeformorder_admissionguidanceprogrammeformtransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdmissionGuidanceFormTransaction',
            fields=[
                ('payment_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('method', models.CharField(blank=True, max_length=50, null=True)),
                ('amount', models.IntegerField()),
                ('card_id', models.CharField(blank=True, max_length=50, null=True)),
                ('bank', models.CharField(blank=True, max_length=50, null=True)),
                ('wallet', models.CharField(blank=True, max_length=50, null=True)),
                ('order_id', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.IntegerField()),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='AdmissionGuidanceFormOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('order_id', models.CharField(db_index=True, max_length=50)),
                ('signature', models.CharField(blank=True, max_length=255, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('payment_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.AdmissionGuidanceFormTransaction')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_order', to='miscs.AdmissionGuidance')),
            ],
        ),
    ]
