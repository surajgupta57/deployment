# Generated by Django 2.2.10 on 2022-04-08 11:46

import categories.util
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PopupCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=75)),
                ('image', models.ImageField(help_text='image size should be 1180x720 pixels', upload_to=categories.util.popup_category_thumbnail_upload_path)),
                ('link', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'Popup Category',
                'verbose_name_plural': 'Popup Category',
            },
        ),
    ]
