# Generated by Django 2.2.10 on 2022-06-23 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0114_auto_20220608_1652'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='phone_number_cannot_viewed',
            field=models.BooleanField(default=False, verbose_name='Phone Number Cannot Viewed Permission'),
        ),
    ]
