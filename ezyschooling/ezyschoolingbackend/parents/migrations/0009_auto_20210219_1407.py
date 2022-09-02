# Generated by Django 2.2.10 on 2021-02-19 08:37

from django.db import migrations, models
import parents.utils


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0008_parentprofile_aadhaar_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentprofile',
            name='pan_card_proof',
            field=models.ImageField(blank=True, null=True, upload_to=parents.utils.parent_pan_card_path),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='parent_aadhar_card',
            field=models.ImageField(blank=True, null=True, upload_to=parents.utils.parent_addhar_card_path),
        ),
    ]