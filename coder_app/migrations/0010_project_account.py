# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-12 20:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_auto_20180107_1206'),
        ('coder_app', '0009_project_is_frozen'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='account',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='common.Account'),
        ),
    ]
