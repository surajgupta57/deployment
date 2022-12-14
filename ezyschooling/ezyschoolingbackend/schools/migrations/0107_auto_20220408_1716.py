# Generated by Django 2.2.10 on 2022-04-08 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0106_auto_20220408_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='for_homepage',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='sending_email_ids',
            field=models.TextField(blank=True, null=True),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]
