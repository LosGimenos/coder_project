# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-02 18:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0010_project_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
