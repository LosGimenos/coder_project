# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-08 21:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0004_auto_20171108_2053'),
    ]

    operations = [
        migrations.AddField(
            model_name='coder',
            name='username',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]