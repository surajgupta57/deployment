# Generated by Django 2.2.10 on 2022-01-27 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0087_auto_20220113_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='avg_fee',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]