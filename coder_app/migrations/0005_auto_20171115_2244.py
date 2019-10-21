# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-15 22:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0004_row_curr_col_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='row',
            name='is_instagram',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='row',
            name='is_twitter',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='row',
            name='media_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='row',
            name='media_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]