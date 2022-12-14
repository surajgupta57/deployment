# Generated by Django 2.2.10 on 2021-11-09 07:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('tags', '0002_customtag_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomSkillTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug')),
                ('featured', models.BooleanField(default=False)),
                ('similar_tag', models.ManyToManyField(blank=True, related_name='_customskilltag_similar_tag_+', to='tags.CustomSkillTag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SkillTagged',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.IntegerField(db_index=True, verbose_name='Object id')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags_skilltagged_tagged_items', to='contenttypes.ContentType', verbose_name='Content type')),
                ('tag', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tags_skilltagged_items', to='tags.CustomSkillTag')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
