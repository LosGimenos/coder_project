# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-04 21:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0010_row_adverse_event_datetime'),
    ]

    operations = [
        migrations.RenameField(
            model_name='row',
            old_name='adverse_event_datetime',
            new_name='adverse_event_datetime_submitted',
        ),
    ]
