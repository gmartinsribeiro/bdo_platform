# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-11-27 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bdo_main_app', '0004_auto_20170922_1341'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='name',
        ),
        migrations.AlterField(
            model_name='service',
            name='job_name',
            field=models.CharField(max_length=100),
        ),
    ]
