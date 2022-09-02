# Generated by Django 2.2.10 on 2020-04-13 07:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0004_auto_20200402_1742'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetitionCarouselCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Competition Carousel Categories',
            },
        ),
        migrations.CreateModel(
            name='CompetitionCarousel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_name', models.CharField(max_length=200)),
                ('child_name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('image', models.ImageField(upload_to='competition/')),
                ('order', models.IntegerField(default=0)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='miscs.CompetitionCarouselCategory')),
            ],
            options={
                'verbose_name_plural': 'Competition Carousel Categories',
            },
        ),
    ]