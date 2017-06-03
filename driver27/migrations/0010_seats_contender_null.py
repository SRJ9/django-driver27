# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def seats_contender_null(apps, schema_editor):
    Seat = apps.get_model("driver27", "Seat")
    for seat in Seat.objects.all():
        seat.contender = None
        seat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0009_populate_driver_in_seats'),
        ]

    operations = [
        migrations.RunPython(
            seats_contender_null,
        ),
    ]