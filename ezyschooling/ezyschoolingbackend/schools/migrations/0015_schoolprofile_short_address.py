# Generated by Django 2.2.10 on 2020-08-27 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0014_auto_20200819_0400'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='short_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
