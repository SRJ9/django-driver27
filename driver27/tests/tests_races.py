from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import GrandPrix, Season, Competition, Race

class RaceTestCase(TestCase):

    fixtures = ['competition.json', 'circuits-2016.json', 'grands-prix.json', 'seasons-2016.json']

    def test_if_bahrein_gp_is_allowed_in_moto_gp_season(self):
        """ GrandPrix are limited for their competitions.
            Bahrein is a F1 team.
            Bahrein is not allowed in MotoGP Season.
        """
        # competitions
        formula_one = Competition.objects.get(pk=1)
        moto_gp = Competition.objects.get(pk=2)

        # bahrein gp
        bahrein_gp = GrandPrix.objects.get(pk=2)
        self.assertTrue(moto_gp not in bahrein_gp.competitions.all(), 'Bahrein is not a Moto GP Grand Prix')

        # season 2017 MotoGP
        season = Season.objects.create(year=2017, competition=moto_gp)

        self.assertRaises(ValidationError, Race.objects.create,
                          **{"season":season,"round":1, "grand_prix": bahrein_gp})
