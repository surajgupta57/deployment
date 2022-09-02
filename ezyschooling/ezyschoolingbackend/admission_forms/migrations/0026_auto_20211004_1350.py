# Generated by Django 2.2.10 on 2021-10-04 08:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0025_auto_20211004_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationform',
            name='session',
            field=models.CharField(blank=True, default='2020-2021', help_text='ex 2021-2022, 2022-2023', max_length=9, null=True, validators=[django.core.validators.RegexValidator(code='nomatch', message='Please Input Correct Format', regex='^.{9}$')], verbose_name='Session'),
        ),
        migrations.AddField(
            model_name='commonregistrationformafterpayment',
            name='session',
            field=models.CharField(blank=True, default='2020-2021', help_text='ex 2021-2022, 2022-2023', max_length=9, null=True, validators=[django.core.validators.RegexValidator(code='nomatch', message='Please Input Correct Format', regex='^.{9}$')], verbose_name='Session'),
        ),
    ]