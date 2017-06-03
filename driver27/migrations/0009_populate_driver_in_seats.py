# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_driver_in_seats(apps, schema_editor):
    Seat = apps.get_model("driver27", "Seat")
    for seat in Seat.objects.all():
        driver = seat.contender.driver
        seat.driver = driver
        seat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0008_auto_20170529_2220'),
        ]

    operations = [
        migrations.RunPython(
            populate_driver_in_seats,
        ),
    ]