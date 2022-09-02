# Generated by Django 2.2.10 on 2020-04-02 12:12

from django.db import migrations, models
import miscs.utils


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0003_auto_20200402_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='image',
            field=models.ImageField(blank=True, max_length=200, null=True, upload_to=miscs.utils.activity_image_upload_path),
        ),
        migrations.AlterField(
            model_name='activity',
            name='videos',
            field=models.FileField(blank=True, null=True, upload_to=miscs.utils.activity_video_upload_path),
        ),
        migrations.AlterField(
            model_name='ezyschoolingnewsarticle',
            name='image',
            field=models.ImageField(upload_to=miscs.utils.ezyschooling_new_article_image_upload_path),
        ),
    ]