# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-02 20:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0005_auto_20171220_0005'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'permissions': (('is_coding_app_admin', 'Is admin for Coding App'),)},
        ),
    ]
