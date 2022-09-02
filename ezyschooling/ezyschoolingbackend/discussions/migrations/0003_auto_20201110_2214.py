# Generated by Django 2.2.16 on 2020-11-10 16:44

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussions', '0002_auto_20200810_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discussioncomment',
            name='likes',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='user_liked_discussion_comments', to=settings.AUTH_USER_MODEL),
        ),
    ]
