# Generated by Django 2.2.10 on 2022-08-01 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0037_auto_20220705_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='childschoolcart',
            name='coupon_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='childschoolcart',
            name='discount',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='convenience_fee',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='coupon_applied_on',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='coupon_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='coupon_discount',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='ezyschool_commission',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='ezyschool_commission_percentage',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='ezyschool_total_amount',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='form_fee',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='school_settlement_amount',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
