# Generated by Django 2.2.10 on 2020-06-30 15:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0008_auto_20200625_2200'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.State'),
        ),
    ]
