# Generated by Django 2.2.10 on 2020-08-28 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertuservideo',
            name='youtube_views',
            field=models.PositiveIntegerField(default=0),
        ),
    ]