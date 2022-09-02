# Generated by Django 2.2.10 on 2020-08-10 15:40

from django.db import migrations, models
import django.db.models.deletion
import parents.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admission_informations', '0001_initial'),
        ('discussions', '0001_initial'),
        ('schools', '0011_auto_20200720_1520'),
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(max_length=250)),
                ('city', models.CharField(max_length=150)),
                ('state', models.CharField(max_length=100)),
                ('pincode', models.CharField(max_length=10)),
                ('country', models.CharField(max_length=150)),
                ('phone_no', models.CharField(max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Parent Address',
                'verbose_name_plural': 'Parent Address',
            },
        ),
        migrations.CreateModel(
            name='ParentProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('name', models.CharField(max_length=150)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(choices=[('male', 'male'), ('female', 'female')], default='male', max_length=10)),
                ('slug', models.SlugField(blank=True, max_length=180, null=True, unique=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to=parents.utils.parent_profile_picture_upload_path)),
                ('income', models.CharField(blank=True, max_length=12, null=True)),
                ('phone', models.CharField(blank=True, max_length=30, null=True)),
                ('bio', models.CharField(blank=True, max_length=255, null=True)),
                ('parent_type', models.CharField(blank=True, max_length=50, null=True)),
                ('education', models.CharField(blank=True, max_length=255, null=True)),
                ('occupation', models.CharField(blank=True, max_length=255, null=True)),
                ('office_address', models.CharField(blank=True, max_length=255, null=True)),
                ('office_number', models.CharField(blank=True, max_length=15, null=True)),
                ('alumni_year_of_passing', models.CharField(blank=True, max_length=5, null=True)),
                ('passing_class', models.CharField(blank=True, max_length=5, null=True)),
                ('alumni_proof', models.ImageField(blank=True, null=True, upload_to='images')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('alumni_school_name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_name', to='schools.SchoolProfile')),
                ('bookmarked_admission_articles', models.ManyToManyField(blank=True, related_name='bookmarked_parents', to='admission_informations.AdmissionInformationArticle')),
                ('bookmarked_admission_videos', models.ManyToManyField(blank=True, related_name='bookmarked_parents', to='admission_informations.AdmissionInformationUserVideo')),
                ('bookmarked_articles', models.ManyToManyField(blank=True, related_name='bookmarked_parents', to='articles.ExpertArticle')),
                ('bookmarked_discussions', models.ManyToManyField(blank=True, related_name='bookmarked_parents', to='discussions.Discussion')),
            ],
            options={
                'verbose_name': 'Parent Profile',
                'verbose_name_plural': 'Parent Profiles',
            },
        ),
    ]
