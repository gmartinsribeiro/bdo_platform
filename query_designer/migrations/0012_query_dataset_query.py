# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-18 13:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0015_dataset_dataset_user'),
        ('query_designer', '0011_auto_20180716_1704'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='dataset_query',
            field=models.ManyToManyField(to='aggregator.Dataset'),
        ),
    ]
