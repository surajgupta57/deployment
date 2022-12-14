# Generated by Django 2.2.10 on 2021-02-19 08:37

import admission_forms.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0011_commonregistrationform_extra_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='commonregistrationform',
            name='baptism_certificate',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.baptism_certificate_upload_path),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='differently_abled_proof',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.differently_abled_upload_path),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='distance_affidavit',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.distance_affidavit_upload_path),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='family_photo',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.family_photo_upload_path),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='mother_tounge',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='commonregistrationform',
            name='parent_signature_upload',
            field=models.ImageField(blank=True, null=True, upload_to=admission_forms.utils.parent_signature_upload_path),
        ),
    ]
