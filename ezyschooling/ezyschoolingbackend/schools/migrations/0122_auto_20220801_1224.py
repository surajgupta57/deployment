# Generated by Django 2.2.10 on 2022-08-01 06:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0121_auto_20220730_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='commission_percentage',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.CreateModel(
            name='Coupons',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_code', models.CharField(blank=True, max_length=100, null=True)),
                ('school_amount', models.FloatField(blank=True, null=True)),
                ('school_coupon_type', models.CharField(choices=[('P', 'Percentage'), ('F', 'Flat')], default=None, max_length=10)),
                ('ezyschool_code', models.CharField(blank=True, max_length=100, null=True)),
                ('ezyschool_amount', models.FloatField(blank=True, null=True)),
                ('ezyschool_coupon_type', models.CharField(choices=[('P', 'Percentage'), ('F', 'Flat')], default=None, max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('school', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, related_name='coupon', to='schools.SchoolProfile')),
            ],
        ),
    ]
