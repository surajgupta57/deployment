# Generated by Django 2.2.10 on 2021-11-22 07:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('schools', '0076_auto_20211122_1327'),
    ]

    operations = [
        migrations.CreateModel(
            name='CityDistrictSchoolTypeFaq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft Faq'), ('Published', 'Published Faq')], default='Draft', max_length=15, null=True)),
                ('is_popular', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=15, null=True)),
                ('faq_answer', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.City')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.District')),
                ('school_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolType')),
            ],
            options={
                'verbose_name': 'City / District - School Type FAQ',
                'verbose_name_plural': 'City / District - School Type FAQs',
            },
        ),
        migrations.CreateModel(
            name='CityDistrictGradeFaq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft Faq'), ('Published', 'Published Faq')], default='Draft', max_length=15, null=True)),
                ('is_popular', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=15, null=True)),
                ('faq_answer', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.City')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.District')),
                ('grade', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolClasses')),
            ],
            options={
                'verbose_name': 'City / District - Grade FAQ',
                'verbose_name_plural': 'City / District - Grade FAQs',
            },
        ),
        migrations.CreateModel(
            name='CityDistrictFaq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft Faq'), ('Published', 'Published Faq')], default='Draft', max_length=15, null=True)),
                ('is_popular', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=15, null=True)),
                ('faq_answer', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.City')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.District')),
            ],
            options={
                'verbose_name': 'City / District - FAQ',
                'verbose_name_plural': 'City / District - FAQs',
            },
        ),
        migrations.CreateModel(
            name='CityDistrictCoedFaq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft Faq'), ('Published', 'Published Faq')], default='Draft', max_length=15, null=True)),
                ('school_category', models.CharField(blank=True, choices=[('Girls', 'Girls'), ('Boys', 'Boys'), ('Coed', 'Coed')], default='Coed', max_length=10, null=True)),
                ('is_popular', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=15, null=True)),
                ('faq_answer', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.City')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.District')),
            ],
            options={
                'verbose_name': 'City / District - Coed FAQ',
                'verbose_name_plural': 'City / District - Coed FAQs',
            },
        ),
        migrations.CreateModel(
            name='CityDistrictBoardFaq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft Faq'), ('Published', 'Published Faq')], default='Draft', max_length=15, null=True)),
                ('is_popular', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=15, null=True)),
                ('faq_answer', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.City')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.District')),
                ('school_board', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolBoard')),
            ],
            options={
                'verbose_name': 'City / District - Board FAQ',
                'verbose_name_plural': 'City / District - Board FAQs',
            },
        ),
    ]
