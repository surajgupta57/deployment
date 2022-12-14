# Generated by Django 2.2.10 on 2021-02-21 17:25

from django.db import migrations, models
import parents.utils


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0009_auto_20210219_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentprofile',
            name='designation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='profession',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='special_ground',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='special_ground_proof',
            field=models.ImageField(blank=True, null=True, upload_to=parents.utils.parent_special_ground_proof),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='transferable_job',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
