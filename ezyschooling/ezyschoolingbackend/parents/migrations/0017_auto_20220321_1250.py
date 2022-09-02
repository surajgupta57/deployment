# Generated by Django 2.2.10 on 2022-03-21 07:20

from django.db import migrations, models
import parents.utils


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0016_auto_20220214_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentprofile',
            name='alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='parentprofile',
            name='covid_vaccination_certificate',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='parentprofile',
            name='pan_card_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_pan_card_path),
        ),
        migrations.AlterField(
            model_name='parentprofile',
            name='parent_aadhar_card',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_addhar_card_path),
        ),
        migrations.AlterField(
            model_name='parentprofile',
            name='special_ground_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_special_ground_proof),
        ),
    ]
