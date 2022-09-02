# Generated by Django 2.2.10 on 2022-07-30 06:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0120_auto_20220723_1114'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolenquiry',
            name='child_name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='schoolenquiry',
            name='interested_for_visit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='schoolenquiry',
            name='second_number',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='schoolenquiry',
            name='second_number_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='schoolenquiry',
            name='tentative_date_of_visit',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='schoolenquiry',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
