# Generated by Django 2.2.10 on 2022-01-03 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0085_auto_20220103_1606'),
        ('news', '0003_news_for_home_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='for_schools',
            field=models.ManyToManyField(blank=True, to='schools.SchoolProfile'),
        ),
    ]
