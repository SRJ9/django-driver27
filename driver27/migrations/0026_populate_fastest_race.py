# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_fastest_lap(apps, schema_editor):
    Race = apps.get_model("driver27", "Race")
    for race in Race.objects.all():
        fastest = race.results.filter(fastest_lap=True).first()
        if fastest:
            race.fastest_car = fastest.seat
            race.save()


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0025_auto_20171022_2012'),
        ]

    operations = [
        migrations.RunPython(
            populate_fastest_lap,
        ),
    ]