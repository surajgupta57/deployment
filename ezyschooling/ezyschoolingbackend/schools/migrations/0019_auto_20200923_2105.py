# Generated by Django 2.2.10 on 2020-09-23 15:35

from django.db import migrations, models
import django.db.models.deletion
import schools.utils


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0018_region_is_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolFormat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField()),
                ('photo', models.ImageField(blank=True, null=True, upload_to=schools.utils.school_region_photo_upload_path)),
            ],
            options={
                'verbose_name': 'School Format',
                'verbose_name_plural': 'School Formats',
            },
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='school_format',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolFormat'),
        ),
    ]