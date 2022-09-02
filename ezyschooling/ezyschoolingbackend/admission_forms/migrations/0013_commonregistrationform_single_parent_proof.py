# Generated by Django 2.2.10 on 2021-02-19 08:49

import admission_forms.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0012_auto_20210219_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationform',
            name='single_parent_proof',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.single_parent_proof_upload_path),
        ),
    ]
