# Generated by Django 2.2.10 on 2021-05-26 10:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0049_city_is_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'verbose_name': 'Feature Name',
                'verbose_name_plural': 'Feature Names',
            },
        ),
        migrations.CreateModel(
            name='Subfeature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feature_subfeature', to='schools.FeatureName')),
            ],
            options={
                'verbose_name': 'Feature Name (Sub)',
                'verbose_name_plural': 'Feature Names (Sub)',
            },
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exist', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No'), ('Undefined', 'Undefined')], default='Undefined', max_length=15, null=True)),
                ('features', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.Subfeature')),
                ('school', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'School Features Sets',
                'verbose_name_plural': 'School Features Sets',
            },
        ),
    ]
