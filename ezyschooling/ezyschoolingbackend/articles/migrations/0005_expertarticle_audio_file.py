# Generated by Django 2.2.16 on 2021-06-15 06:48

import articles.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0004_expertarticle_meta_desc'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertarticle',
            name='audio_file',
            field=models.FileField(blank=True, null=True, upload_to=articles.utils.expert_article_audio_upload_path),
        ),
    ]
