# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-09-19 13:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0009_update_distributions'),
    ]

    operations = [
        migrations.AddField(
            model_name='dimension',
            name='non_filterable',
            field=models.BooleanField(default=False),
        ),
    ]
