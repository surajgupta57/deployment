# Generated by Django 2.2.10 on 2022-03-05 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0101_auto_20220303_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='online_school',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]