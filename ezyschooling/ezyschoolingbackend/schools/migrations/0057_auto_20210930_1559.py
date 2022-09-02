# Generated by Django 2.2.10 on 2021-09-30 10:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0056_auto_20210930_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feestructure',
            name='session',
            field=models.CharField(default='2020-2021', help_text='ex 2021-2022, 2022-2023', max_length=9, validators=[django.core.validators.RegexValidator(code='nomatch', message='Please Input Correct Format', regex='^.{9}$')], verbose_name='Session'),
        ),
    ]