from django.test import TestCase, Client, RequestFactory
# from django.core.urlresolvers import reverse

from django.contrib.admin.sites import AdminSite
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from ..models import Season, Driver, Team, Competition, Circuit, GrandPrix, Race, Contender, Result
from ..admin import SeasonAdmin, DriverAdmin, TeamAdmin, CompetitionAdmin, CircuitAdmin, GrandPrixAdmin, \
    RaceAdmin, ContenderAdmin, RelatedCompetitionAdmin, RaceInline

class MockRequest(object):
    pass

request = MockRequest()

class AdminTest(TestCase):
    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json', 'teams-season.json', 'driver-competition-2016.json', 'driver-competition-team-2016.json',
    'races-2016.json', 'results-2016.json']

    def setUp(self):
        self.site = AdminSite()
        self.client = Client()
        self.factory = RequestFactory()

    def test_season_admin(self):
        ma = SeasonAdmin(Season, self.site)
        self.assertTrue(ma.get_form(request=None, obj=None))
        season = Season.objects.get(pk=1)
        self.assertTrue(ma.get_form(request=request, obj=season))

    def test_driver_admin(self):
        ma = DriverAdmin(Driver, self.site)
        driver = Driver.objects.get(pk=1)
        self.assertTrue(ma.print_competitions(driver))

    def test_team_admin(self):
        ma = TeamAdmin(Team, self.site)
        team = Team.objects.get(pk=1)
        self.assertTrue(ma.print_competitions(team))

    def test_competition_admin(self):
        ma = CompetitionAdmin(Competition, self.site)

    def test_circuit_admin(self):
        ma = CircuitAdmin(Circuit, self.site)

    def test_grandprix_admin(self):
        ma = GrandPrixAdmin(GrandPrix, self.site)

    def test_race_admin(self):
        ma = RaceAdmin(Race, self.site)
        race = Race.objects.get(pk=1)
        self.assertEquals(ma.print_pole(race), str(race.pole.contender.driver))
        self.assertEquals(ma.print_winner(race), str(race.winner.contender.driver))
        self.assertEquals(ma.print_fastest(race), str(race.fastest.contender.driver))
        self.assertIsNotNone(ma.print_results_link(race))


        request = self.factory.get(reverse("admin:driver27_race_results", args=[race.pk]))
        self.assertTrue(ma.results(request, race.pk))

        race = Race.objects.get(pk=20) # No results
        self.assertIsNone(ma.print_pole(race))
        self.assertIsNone(ma.print_winner(race))
        self.assertIsNone(ma.print_fastest(race))
        self.assertIsNotNone(ma.print_results_link(race))

        request = self.factory.get(reverse("admin:driver27_race_results", args=[race.pk]))
        self.assertTrue(ma.results(request, race.pk))

    def test_contender_admin(self):
        ma = ContenderAdmin(Contender, self.site)
        contender = Contender.objects.get(pk=1)
        self.assertIsNotNone(ma.print_current(contender))

    def test_related_competition_admin(self):
        race = Race.objects.get(pk=1)
        related_competition = RelatedCompetitionAdmin()
        # maybe exception
        self.assertIsNone(related_competition.print_competitions(race))


