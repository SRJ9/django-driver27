from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import Team, Season, Competition, TeamSeasonRel

class TeamTestCase(TestCase):

    fixtures = ['competition.json', 'teams-2016.json', 'seasons-2016.json']

    def test_if_mercedes_can_play_motogp_season(self):
        """ Teams are limited for their competitions.
            Mercedes is a F1 team.
            Mercedes can't start a motoGP season.
        """
        # competitions
        formula_one = Competition.objects.get(pk=1)
        moto_gp = Competition.objects.get(pk=2)

        # team
        mercedes_team = Team.objects.get(pk=1)
        mercedes_team.competitions.add(formula_one)

        # season 2016
        season = Season.objects.create(year=2017, competition=moto_gp)

        self.assertRaises(ValidationError, TeamSeasonRel.objects.create, **{"season":season,"team":mercedes_team})
