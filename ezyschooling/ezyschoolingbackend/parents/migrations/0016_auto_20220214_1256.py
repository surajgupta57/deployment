# Generated by Django 2.2.10 on 2022-02-14 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0015_auto_20211222_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentprofile',
            name='college_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='course_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]