# Generated by Django 2.2.10 on 2021-09-08 05:25

import childs.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0023_auto_20210630_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationformafterpayment',
            name='child_medical_certificate',
            field=models.ImageField(blank=True, null=True, upload_to=childs.utils.medical_fitness_certificate_upload_path),
        ),
    ]
