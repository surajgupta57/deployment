# Generated by Django 2.2.10 on 2022-04-25 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0109_auto_20220422_1821'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='virtual_tour',
            field=models.TextField(blank=True, null=True),
        ),
    ]
