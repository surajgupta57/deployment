# Generated by Django 2.2.10 on 2020-08-10 15:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit_selectize.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tags', '0001_initial'),
        ('parents', '0001_initial'),
        ('categories', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experts', '0001_initial'),
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertarticlecomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_users_expert_article_comment', to='parents.ParentProfile'),
        ),
        migrations.AddField(
            model_name='expertarticlecomment',
            name='parent_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_expert_article_comment_childrens', to='articles.ExpertArticleComment'),
        ),
        migrations.AddField(
            model_name='expertarticle',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_articles', to='categories.Board'),
        ),
        migrations.AddField(
            model_name='expertarticle',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_articles', to='experts.ExpertUserProfile'),
        ),
        migrations.AddField(
            model_name='expertarticle',
            name='likes',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='user_liked_expert_articles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='expertarticle',
            name='sub_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_articles', to='categories.SubCategory'),
        ),
        migrations.AddField(
            model_name='expertarticle',
            name='tags',
            field=taggit_selectize.managers.TaggableManager(help_text='A comma-separated list of tags.', through='tags.Tagged', to='tags.CustomTag', verbose_name='Tags'),
        ),
    ]
