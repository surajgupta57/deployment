# Generated by Django 2.2.10 on 2021-10-05 06:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0064_auto_20211005_1158'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='admmissionopenclasses',
            unique_together={('class_relation', 'school')},
        ),
        migrations.RemoveField(
            model_name='admmissionopenclasses',
            name='session',
        ),
    ]
