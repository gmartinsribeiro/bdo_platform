# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-19 21:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service_builder', '0012_auto_20180518_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='price',
            field=models.CharField(default='free', max_length=50),
        ),
    ]
