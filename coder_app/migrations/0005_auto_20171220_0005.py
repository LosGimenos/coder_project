# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-20 00:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0004_rowmeta_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='columnmeta',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Project'),
        ),
        migrations.AddField(
            model_name='datameta',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Project'),
        ),
    ]
