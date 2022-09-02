# Generated by Django 2.2.10 on 2021-12-22 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0082_auto_20211222_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolpoint',
            name='father_covid_19_frontline_warrior_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='father_covid_vacination_certifiacte_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='guardian_covid_19_frontline_warrior_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='guardian_covid_vacination_certifiacte_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='mother_covid_19_frontline_warrior_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='mother_covid_vacination_certifiacte_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='schoolpoint',
            name='state_transfer_points',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]
