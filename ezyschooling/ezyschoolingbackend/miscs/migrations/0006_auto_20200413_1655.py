# Generated by Django 2.2.10 on 2020-04-13 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0005_competitioncarousel_competitioncarouselcategory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='competitioncarousel',
            options={'verbose_name_plural': 'Competition Carousel'},
        ),
        migrations.AlterField(
            model_name='competitioncarousel',
            name='child_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='competitioncarousel',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='competition/'),
        ),
        migrations.AlterField(
            model_name='competitioncarousel',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='competitioncarousel',
            name='parent_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='competitioncarousel',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='competitioncarouselcategory',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='competitioncarouselcategory',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, null=True, unique=True),
        ),
    ]
