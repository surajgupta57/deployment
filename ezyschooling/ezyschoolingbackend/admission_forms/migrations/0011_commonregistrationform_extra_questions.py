# Generated by Django 2.2.10 on 2021-02-17 07:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0010_schoolapplication_transport_facility_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationform',
            name='extra_questions',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
