from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import Driver, Competition, DriverCompetition, DriverCompetitionTeam, Team, Season

class DriverTestCase(TestCase):

    fixtures = ['drivers-2016.json', 'competition.json', 'driver-competition-2016.json', 'teams-2016.json',
                'teams-competition.json','seasons-2016.json',
                'driver-competition-team-2016.json']

    @staticmethod
    def get_test_driver_A():
        return {'last_name':'McQueen', 'first_name':'Lightning', 'year_of_birth': 2105, 'country':'US'}

    @staticmethod
    def get_test_driver_B():
        return {'last_name':'Frederick', 'first_name':'Flintstone', 'year_of_birth': 1884, 'country':'US'}

    @staticmethod
    def get_test_driver_C():
        return {'last_name':'Fangio', 'first_name':'Manuel', 'year_of_birth': 2000, 'country':'AR'}

    def test_check_year_of_birth(self):
        """ Check year_of_birth limits"""
        self.assertRaises(ValidationError, Driver.objects.create, **self.get_test_driver_A())
        self.assertRaises(ValidationError, Driver.objects.create, **self.get_test_driver_B())
        self.assertTrue(Driver.objects.create(**self.get_test_driver_C()))


    def test_if_hamilton_can_start_moto_gp_season(self):
        hamilton = Driver.objects.get(pk=1)
        formula_one = Competition.objects.get(pk=1)
        hamilton_f1 = DriverCompetition.objects.get(driver=hamilton, competition=formula_one)
        mercedes_team = Team.objects.get(pk=1)
        hamilton_mercedes = DriverCompetitionTeam.objects.get(team=mercedes_team, enrolled=hamilton_f1)

        moto_gp = Competition.objects.get(pk=2)
        season = Season.objects.create(year=2017, competition=moto_gp)

        self.assertRaises(ValidationError, hamilton_mercedes.seasons.add, season)