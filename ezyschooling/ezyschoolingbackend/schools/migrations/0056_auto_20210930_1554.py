# Generated by Django 2.2.10 on 2021-09-30 10:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0055_feestructure_session'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='feestructure',
            unique_together={('class_relation', 'stream_relation', 'school', 'session')},
        ),
    ]
