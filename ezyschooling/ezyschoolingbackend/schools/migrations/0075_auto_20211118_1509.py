# Generated by Django 2.2.10 on 2021-11-18 09:39

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schools', '0074_auto_20211115_1417'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolclassnotification',
            name='notification_sent',
            field=models.BooleanField(default=False),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
        migrations.AlterUniqueTogether(
            name='schoolclassnotification',
            unique_together={('school', 'user', 'notify_class', 'session')},
        ),
    ]
