# Generated by Django 2.2.10 on 2021-02-18 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0036_schoolpoint_transport_facility_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distancepoint',
            name='end',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='distancepoint',
            name='start',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
