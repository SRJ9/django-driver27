# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-27 15:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0002_grandprix'),
    ]

    operations = [
        migrations.RenameField(
            model_name='circuit',
            old_name='year_of_built',
            new_name='opened_in',
        ),
    ]
