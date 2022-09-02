# Generated by Django 2.2.10 on 2022-03-05 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0103_auto_20220311_1106'),
        ('admin_custom', '0002_counselorcadminuser'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='counselorcadminuser',
            name='state',
        ),
        migrations.RemoveField(
            model_name='counselorcadminuser',
            name='city',
        ),
        migrations.AddField(
            model_name='counselorcadminuser',
            name='city',
            field=models.ManyToManyField(to='schools.City'),
        ),
        migrations.RemoveField(
            model_name='counselorcadminuser',
            name='district',
        ),
        migrations.AddField(
            model_name='counselorcadminuser',
            name='district',
            field=models.ManyToManyField(to='schools.District'),
        ),
        migrations.RemoveField(
            model_name='counselorcadminuser',
            name='district_region',
        ),
        migrations.AddField(
            model_name='counselorcadminuser',
            name='district_region',
            field=models.ManyToManyField(to='schools.DistrictRegion'),
        ),
    ]