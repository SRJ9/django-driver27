from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import Team, Season, Competition, TeamSeason, Driver, Contender, Seat

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

        self.assertRaises(ValidationError, TeamSeason.objects.create, **{"season":season,"team":mercedes_team})

    def test_if_pedrosa_can_drive_mercedes_car(self):
        # competitions
        formula_one = Competition.objects.get(pk=1)
        moto_gp = Competition.objects.get(pk=2)

        pedrosa = Driver.objects.create(last_name='Pedrosa', first_name='Dani', year_of_birth=1985, country='ES')
        pedrosa_moto_gp = Contender.objects.create(driver=pedrosa, competition=moto_gp)

        # team
        mercedes_team = Team.objects.get(pk=1)
        mercedes_team.competitions.add(formula_one)

        self.assertRaises(ValidationError, Seat.objects.create,
                          **{"team": mercedes_team, 'contender': pedrosa_moto_gp, 'current': True})


