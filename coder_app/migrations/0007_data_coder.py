# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-16 20:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0006_auto_20171116_1710'),
    ]

    operations = [
        migrations.AddField(
            model_name='data',
            name='coder',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coder_app.Coder'),
        ),
    ]