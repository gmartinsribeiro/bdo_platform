# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-13 12:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0003_auto_20170513_1222'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dimension',
            name='data_column_name',
        ),
        migrations.RemoveField(
            model_name='variable',
            name='data_table_name',
        ),
    ]
