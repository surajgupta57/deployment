# Generated by Django 2.2.10 on 2022-03-11 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0102_auto_20220305_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolprofile',
            name='calculated_avg_fee',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='last_avg_fee_calculated',
            field=models.DateField(blank=True, null=True),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]
