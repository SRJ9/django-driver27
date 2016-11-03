from django.test import TestCase, Client, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.conf import settings
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from ..models import Season, Driver, Team, Competition, Circuit, GrandPrix, Race, Contender, Result, Seat, TeamSeason
from ..admin import SeasonAdmin, SeasonAdminForm, DriverAdmin, TeamAdmin, CompetitionAdmin, CircuitAdmin, GrandPrixAdmin, \
    RaceAdmin, ContenderAdmin, RelatedCompetitionAdmin, RaceInline, SeatInline, SeatSeasonInline, TeamSeasonInline

class MockRequest(object):
    pass

class MockSuperUser(object):
    def has_perm(self, perm):
        return True

def get_request():
    request = MockRequest()
    request.user = MockSuperUser()
    return request


def get_fixtures_test():
    # django test uses a new db, while pytest use transaction no_commit in the same settings db
    if hasattr(settings, 'PYTEST_SETTING') and settings.PYTEST_SETTING:
        return None
    else:
        return ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
                'seasons-2016.json', 'teams-2016.json', 'teams-season.json', 'driver-competition-2016.json',
                'driver-competition-team-2016.json',
                'races-2016.json', 'results-2016.json']


class FixturesTest(TestCase):
    fixtures = get_fixtures_test()

class ViewTest(FixturesTest):

    def setUp(self):
        self.site = AdminSite()
        self.client = Client()
        self.factory = RequestFactory()



    def test_competition_list(self):
        # Issue a GET request.
        response = self.client.get(reverse('competition-list'))

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_competition_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('competition-view', kwargs={'competition_slug': 'f1'}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('competition-view', kwargs={'competition_slug': 'f19'}))
        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_season_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('season-view', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-driver', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-team', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-race-list', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-view', kwargs={'competition_slug': 'f19', 'year': 2006}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 404)

    def test_race_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('season-race-view', kwargs={'competition_slug': 'f1', 'year': 2016, 'race_id':1}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)
        # Issue a GET request.
        response = self.client.get(reverse('season-race-view', kwargs={'competition_slug': 'f1', 'year': 2016, 'race_id': 200}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 404)

    # def test_admin(self):
    #     response = self.client.get(reverse('admin:driver27_driver_changelist'))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)
    #
    #     response = self.client.get(reverse('admin:driver27_driver_change', args=[1]))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)
    #
    #     response = self.client.get(reverse('admin:driver27_season_changelist'))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)
    #
    #     response = self.client.get(reverse('admin:driver27_season_change', args=[1]))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)
    #
    #     response = self.client.get(reverse('admin:driver27_race_changelist'))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)
    #
    #     response = self.client.get(reverse('admin:driver27_race_change', args=[1]))
    #     # Check that the response is 200 OK.
    #     self.assertEqual(response.status_code, 302)

    def _check_get_changelist(self, ma):
        request = get_request()
        self.assertTrue(ma.get_changelist(request=request))


    def test_season_admin(self):
        ma = SeasonAdmin(Season, self.site)
        self._check_get_changelist(ma)
        self.assertTrue(ma.get_form(request=None, obj=None))

        request = get_request()
        season = Season.objects.get(pk=1)
        season_form = ma.get_form(request=request, obj=season)
        self.assertIsNotNone(SeasonAdminForm(season_form))

    def test_driver_admin(self):
        ma = DriverAdmin(Driver, self.site)
        self._check_get_changelist(ma)
        driver = Driver.objects.get(pk=1)
        self.assertTrue(ma.print_competitions(driver))

    def test_team_admin(self):
        ma = TeamAdmin(Team, self.site)
        self._check_get_changelist(ma)
        team = Team.objects.get(pk=1)
        self.assertTrue(ma.print_competitions(team))

    def test_competition_admin(self):
        ma = CompetitionAdmin(Competition, self.site)
        self._check_get_changelist(ma)

    def test_circuit_admin(self):
        ma = CircuitAdmin(Circuit, self.site)
        self._check_get_changelist(ma)

    def test_grandprix_admin(self):
        ma = GrandPrixAdmin(GrandPrix, self.site)
        self._check_get_changelist(ma)

    def test_race_admin(self):
        ma = RaceAdmin(Race, self.site)
        self._check_get_changelist(ma)
        race = Race.objects.get(pk=1)
        self.assertEquals(ma.print_pole(race), str(race.pole.contender.driver))
        self.assertEquals(ma.print_winner(race), str(race.winner.contender.driver))
        self.assertEquals(ma.print_fastest(race), str(race.fastest.contender.driver))
        self.assertIsNotNone(ma.print_results_link(race))
        self.assertEquals(ma.clean_qualifying('1'), 1)
        self.assertIsNone(ma.clean_qualifying(''))
        self.assertEquals(ma.clean_finish('1'), 1)
        self.assertIsNone(ma.clean_finish(''))

        request = self.factory.get(reverse("admin:driver27_race_results", args=[race.pk]))
        self.assertTrue(ma.results(request, race.pk))

        race_ma = RaceInline(SeasonAdmin, self.site)
        self.assertIsNotNone(race_ma.print_results_link(race))


        request = get_request()
        season = race.season
        request._obj_ = season
        self.assertIsNotNone(race_ma.formfield_for_foreignkey(Race.grand_prix.field, request=request))

        race = Race.objects.get(pk=20) # No results
        self.assertIsNone(ma.print_pole(race))
        self.assertIsNone(ma.print_winner(race))
        self.assertIsNone(ma.print_fastest(race))
        self.assertIsNotNone(ma.print_results_link(race))

        request = self.factory.get(reverse("admin:driver27_race_results", args=[race.pk]))
        self.assertTrue(ma.results(request, race.pk))

    def test_contender_admin(self):
        ma = ContenderAdmin(Contender, self.site)
        self._check_get_changelist(ma)
        contender = Contender.objects.get(pk=1)
        self.assertIsNotNone(ma.print_current(contender))
        request = get_request()
        self.assertTrue(ma.get_form(request=request, obj=contender))

    def _check_formfield_for_foreignkey(self, ma, request_obj, dbfield):
        request = get_request()
        request._obj_ = request_obj
        self.assertIsNotNone(ma.formfield_for_foreignkey(dbfield, request=request))


    def test_seat_inline_admin(self):
        ma = SeatInline(ContenderAdmin, self.site)
        contender = Contender.objects.get(pk=1)
        self._check_formfield_for_foreignkey(ma, request_obj=contender, dbfield=Seat.team.field)

    def test_seat_season_inline_admin(self):
        ma = SeatSeasonInline(SeasonAdmin, self.site)
        season = Season.objects.get(pk=1)
        self._check_formfield_for_foreignkey(ma, request_obj=season, dbfield=Seat.seasons.through.seat.field)

    def test_team_season_inline_admin(self):
        ma = TeamSeasonInline(SeasonAdmin, self.site)
        season = Season.objects.get(pk=1)
        self._check_formfield_for_foreignkey(ma, request_obj=season, dbfield=TeamSeason.team.field)

    def test_related_competition_admin(self):
        race = Race.objects.get(pk=1)
        related_competition = RelatedCompetitionAdmin()
        # maybe exception
        self.assertIsNone(related_competition.print_competitions(race))
