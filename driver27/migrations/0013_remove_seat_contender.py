# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-05-29 22:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0012_auto_20170529_2232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seat',
            name='contender',
        ),
    ]
