# Generated by Django 2.2.10 on 2021-12-22 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('childs', '0009_child_medical_certificate'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='intre_state_transfer',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
