# Generated by Django 2.2.10 on 2021-04-27 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0045_auto_20210421_1342'),
    ]

    operations = [
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='school_district',
            new_name='district',
        ),
        migrations.RenameField(
            model_name='schoolprofile',
            old_name='school_district_region',
            new_name='district_region',
        ),
    ]