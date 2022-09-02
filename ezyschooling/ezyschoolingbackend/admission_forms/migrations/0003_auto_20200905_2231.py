# Generated by Django 2.2.10 on 2020-09-05 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0002_auto_20200810_2110'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationform',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True),
        ),
    ]
