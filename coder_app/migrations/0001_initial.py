# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-10 19:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Coder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=300, null=True)),
                ('middle_name', models.CharField(blank=True, max_length=300, null=True)),
                ('last_name', models.CharField(blank=True, max_length=300, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('rating', models.DecimalField(decimal_places=1, default=10.0, max_digits=3)),
                ('username', models.CharField(blank=True, max_length=300, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Column',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.TextField(blank=True, db_index=True, null=True)),
                ('column_number', models.IntegerField(db_index=True, null=True)),
                ('is_binary_variable', models.BooleanField(default=False)),
                ('true_value', models.TextField(blank=True, db_index=True, null=True)),
                ('false_value', models.TextField(blank=True, db_index=True, null=True)),
                ('is_text_variable', models.BooleanField(default=False)),
                ('is_number_variable', models.BooleanField(default=False)),
                ('is_date_variable', models.BooleanField(default=False)),
                ('is_variable', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(blank=True, null=True)),
                ('date', models.DateTimeField(null=True)),
                ('number', models.FloatField(null=True)),
                ('column', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Column')),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset_ID', models.TextField(blank=True, db_index=True, null=True)),
                ('show', models.BooleanField(default=True)),
                ('path', models.TextField(blank=True, null=True)),
                ('dataset_name', models.TextField(blank=True, db_index=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('id_column', models.IntegerField(null=True)),
                ('date_column', models.IntegerField(null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=4)),
                ('metadata', models.TextField(blank=True, null=True)),
                ('contains_adverse_effects', models.BooleanField(default=False)),
                ('coder', models.ManyToManyField(to='coder_app.Coder')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Row',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row_name', models.TextField(blank=True, db_index=True, null=True)),
                ('row_number', models.IntegerField(db_index=True, null=True)),
                ('matches_filters', models.BooleanField(default=True)),
                ('matches_category', models.BooleanField(default=True)),
                ('matches_split', models.BooleanField(default=True)),
                ('matches_split_exclusions', models.BooleanField(default=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Project')),
            ],
        ),
        migrations.CreateModel(
            name='RowStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('is_locked', models.BooleanField(default=False)),
                ('coder', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Coder')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('is_freeform', models.BooleanField(default=False)),
                ('is_multiple_choice', models.BooleanField(default=False)),
                ('freeform_value', models.TextField(blank=True, null=True)),
                ('multiple_choice_option_one', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_two', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_three', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_four', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_five', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_six', models.CharField(blank=True, max_length=2000, null=True)),
                ('multiple_choice_option_seven', models.CharField(blank=True, max_length=2000, null=True)),
                ('column', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Column')),
            ],
        ),
        migrations.CreateModel(
            name='VariableLibrary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('variable', models.ManyToManyField(to='coder_app.Variable')),
            ],
        ),
        migrations.AddField(
            model_name='tag',
            name='variable',
            field=models.ManyToManyField(to='coder_app.Variable'),
        ),
        migrations.AddField(
            model_name='group',
            name='tag',
            field=models.ManyToManyField(to='coder_app.Tag'),
        ),
        migrations.AddField(
            model_name='data',
            name='dataset',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Dataset'),
        ),
        migrations.AddField(
            model_name='data',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Project'),
        ),
        migrations.AddField(
            model_name='data',
            name='row',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Row'),
        ),
        migrations.AddField(
            model_name='column',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Project'),
        ),
        migrations.AlterIndexTogether(
            name='data',
            index_together=set([('project', 'row', 'column')]),
        ),
    ]
