# Generated by Django 2.2.10 on 2022-02-23 06:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0098_auto_20220223_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='contact_data_permission',
            field=models.BooleanField(default=False, verbose_name='School Contact Data Permission'),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]
