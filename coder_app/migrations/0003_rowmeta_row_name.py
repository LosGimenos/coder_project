# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-14 22:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0002_rowmeta_row'),
    ]

    operations = [
        migrations.AddField(
            model_name='rowmeta',
            name='row_name',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
    ]
