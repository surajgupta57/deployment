# Generated by Django 2.2.10 on 2022-08-04 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0123_auto_20220802_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolenquiry',
            name='interested_for_visit_but_no_data_provided',
            field=models.BooleanField(default=False),
        ),
    ]