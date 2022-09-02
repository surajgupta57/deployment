# Generated by Django 2.2.10 on 2020-10-28 19:58

from django.db import migrations, models
import schools.utils


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0022_schoolprofile_ownership'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='photo',
            field=models.FileField(blank=True, null=True, upload_to=schools.utils.school_region_photo_upload_path),
        ),
        migrations.AlterField(
            model_name='schoolformat',
            name='photo',
            field=models.FileField(blank=True, null=True, upload_to=schools.utils.school_format_photo_upload_path),
        ),
    ]