# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-04 21:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0009_data_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='row',
            name='adverse_event_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
