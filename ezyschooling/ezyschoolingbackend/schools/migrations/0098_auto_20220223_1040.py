# Generated by Django 2.2.10 on 2022-02-23 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0097_auto_20220222_1748'),
    ]

    operations = [
        migrations.RenameField(
            model_name='schoolcontactclickdata',
            old_name='count',
            new_name='count_ezyschooling',
        ),
        migrations.AddField(
            model_name='schoolcontactclickdata',
            name='count_school',
            field=models.PositiveIntegerField(default=0),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]