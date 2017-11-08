# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-08 20:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0003_project_variable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coder',
            old_name='name',
            new_name='first_name',
        ),
        migrations.AddField(
            model_name='coder',
            name='last_name',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='coder',
            name='middle_name',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='coder',
            name='rating',
            field=models.DecimalField(decimal_places=1, default=10.0, max_digits=3),
        ),
    ]