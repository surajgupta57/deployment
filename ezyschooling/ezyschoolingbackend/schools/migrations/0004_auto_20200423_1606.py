# Generated by Django 2.2.10 on 2020-04-23 10:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0003_auto_20200404_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolprofile',
            name='required_admission_form_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='required_child_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='required_father_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='required_guardian_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='required_mother_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
