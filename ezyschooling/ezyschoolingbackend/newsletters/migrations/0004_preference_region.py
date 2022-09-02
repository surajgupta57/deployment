# Generated by Django 2.2.16 on 2020-12-17 10:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0027_auto_20201214_1842'),
        ('newsletters', '0003_preference_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='preference',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.Region'),
        ),
    ]