# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-27 10:46
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Wave_energy_converters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image_uri', models.CharField(max_length=200)),
                ('sample_rows', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
    ]
