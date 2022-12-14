# Generated by Django 2.2.16 on 2020-09-24 18:22

from django.db import migrations, models
import schools.utils


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0019_auto_20200923_2105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolformat',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to=schools.utils.school_format_photo_upload_path),
        ),
    ]
