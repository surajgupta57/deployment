# Generated by Django 2.2.16 on 2020-12-03 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0025_schoolprofile_convenience_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='views',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
