# Generated by Django 2.2.10 on 2020-08-26 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0012_carousel_small_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaqCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'FAQ Category',
                'verbose_name_plural': 'FAQ Categories',
            },
        ),
        migrations.CreateModel(
            name='FaqQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='faq_question', to='miscs.FaqCategory')),
            ],
            options={
                'verbose_name': 'FAQ Question',
                'verbose_name_plural': 'FAQ Questions',
            },
        ),
        migrations.CreateModel(
            name='FaqAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faq_answer', to='miscs.FaqQuestion')),
            ],
            options={
                'verbose_name': 'FAQ Answer',
                'verbose_name_plural': 'FAQ Answers',
            },
        ),
    ]