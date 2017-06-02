# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_competition_team(apps, schema_editor):
    Team = apps.get_model("driver27", "Team")
    CompetitionTeam = apps.get_model("driver27", "CompetitionTeam")
    for team in Team.objects.all():
        competitions = team.competitions.all()
        for competition in competitions:
            CompetitionTeam.objects.create(team=team, competition=competition)


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0017_auto_20170602_1526'),
        ]

    operations = [
        migrations.RunPython(
            populate_competition_team,
        ),
    ]