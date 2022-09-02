# Generated by Django 2.2.10 on 2020-08-10 15:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tags', '0001_initial'),
        ('parents', '0001_initial'),
        ('categories', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experts', '0001_initial'),
        ('admission_informations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissioninformationvideocomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_user_admission_video_comments', to='parents.ParentProfile'),
        ),
        migrations.AddField(
            model_name='admissioninformationvideocomment',
            name='parent_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_admission_video_comment_childrens', to='admission_informations.AdmissionInformationVideoComment'),
        ),
        migrations.AddField(
            model_name='admissioninformationvideocomment',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='video_comments', to='admission_informations.AdmissionInformationUserVideo'),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='board_admission_videos', to='categories.Board'),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admission_videos', to='categories.ExpertUserVideoCategory'),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='expert',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_user_admission_videos', to='experts.ExpertUserProfile'),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='likes',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='user_liked_admission_videos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='sub_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_category_admission_vidoes', to='categories.SubCategory'),
        ),
        migrations.AddField(
            model_name='admissioninformationuservideo',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='tags.Tagged', to='tags.CustomTag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='admissioninformationnewsheadline',
            name='news',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='headlines', to='admission_informations.AdmissionInformationNews'),
        ),
        migrations.AddField(
            model_name='admissioninformationnews',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='board_admission_information_news', to='categories.Board'),
        ),
        migrations.AddField(
            model_name='admissioninformationnews',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='tags.Tagged', to='tags.CustomTag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticlecomment',
            name='article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='article_comments', to='admission_informations.AdmissionInformationArticle'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticlecomment',
            name='expert',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expert_users_admission_article_comment', to='experts.ExpertUserProfile'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticlecomment',
            name='likes',
            field=models.ManyToManyField(db_index=True, related_name='user_liked_admission_article_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='admissioninformationarticlecomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_users_admission_article_comment', to='parents.ParentProfile'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticlecomment',
            name='parent_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_admission_article_comment_childrens', to='admission_informations.AdmissionInformationArticleComment'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticle',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admission_articles', to='categories.Board'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticle',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admission_articles', to='experts.ExpertUserProfile'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticle',
            name='likes',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='user_liked_admission_articles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='admissioninformationarticle',
            name='sub_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admission_articles', to='categories.SubCategory'),
        ),
        migrations.AddField(
            model_name='admissioninformationarticle',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='tags.Tagged', to='tags.CustomTag', verbose_name='Tags'),
        ),
    ]
