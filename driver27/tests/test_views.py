from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, Client, RequestFactory

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from ..models import Season, Driver, Team, Competition, Circuit, get_results_tuples
from ..models import GrandPrix, Race, Seat, TeamSeason, ContenderSeason
from ..admin import SeasonAdmin, SeasonAdminForm, DriverAdmin, TeamAdmin
from ..admin import CompetitionAdmin, CircuitAdmin, GrandPrixAdmin
from ..admin import RaceAdmin, RelatedCompetitionAdmin
from ..admin import RaceInline, TeamSeasonInline
from ..admin.formsets import RaceFormSet
from ..admin.common import AlwaysChangedModelForm
from ..punctuation import get_punctuation_config
from rest_framework.test import APITestCase


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
        return ['driver27.json', ]


class FixturesTest(TestCase):
    fixtures = get_fixtures_test()


class ViewTest(FixturesTest):
    def setUp(self):
        self.site = AdminSite()
        self.client = Client()
        self.factory = RequestFactory()

    def _GET_request(self, reverse_url, kwargs=None, code=200):
        # Issue a GET request.
        the_reverse = reverse(reverse_url, kwargs=kwargs)
        response = self.client.get(the_reverse)
        # Check that the response is 302 OK.
        self.assertEqual(response.status_code, code)

    # def test_competition_list(self):
    #     self._GET_request('dr27-competition-list')

    def test_competition_view(self):
        self._GET_request('dr27-competition-view', kwargs={'competition_slug': 'f1'})
        self._GET_request('dr27-competition-driver-olympic', kwargs={'competition_slug': 'f1'})
        self._GET_request('dr27-competition-team-olympic', kwargs={'competition_slug': 'f1'})
        self._GET_request('dr27-competition-view', kwargs={'competition_slug': 'f19'}, code=404)

    def test_season_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016}
        self._GET_request('dr27-season-view', kwargs=kwargs)
        self._GET_request('dr27-season-driver', kwargs=kwargs)
        self._GET_request('dr27-season-driver-olympic', kwargs=kwargs)
        self._GET_request('dr27-season-team', kwargs=kwargs)
        self._GET_request('dr27-season-team-olympic', kwargs=kwargs)
        self._GET_request('dr27-season-race-list', kwargs=kwargs)

        kwargs = {'competition_slug': 'f19', 'year': 2006}
        self._GET_request('dr27-season-view', kwargs=kwargs, code=404)

    def test_race_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016, 'race_id': 1}
        self._GET_request('dr27-season-race-view', kwargs=kwargs)
        kwargs['race_id'] = 200
        self._GET_request('dr27-season-race-view', kwargs=kwargs, code=404)

    def _test_driver_record_view(self, base_path, kwargs):
        self._GET_request(base_path+'-driver-record-index', kwargs=kwargs)
        kwargs['record'] = 'POLE'
        self._GET_request(base_path+'-driver-record', kwargs=kwargs)
        self._GET_request(base_path+'-driver-streak', kwargs=kwargs)
        self._GET_request(base_path+'-driver-top-streak', kwargs=kwargs)
        self._GET_request(base_path+'-driver-active-streak', kwargs=kwargs)
        self._GET_request(base_path+'-driver-active-top-streak', kwargs=kwargs)

        if base_path == 'dr27-competition' or base_path == 'dr27-global':
            self._GET_request(base_path+'-driver-seasons', kwargs=kwargs)

        kwargs['record'] = 'FFF'
        self._GET_request(base_path+'-driver-record', kwargs=kwargs, code=404)

    def test_driver_records_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016}
        self._test_driver_record_view('dr27-season', kwargs)

    def test_driver_records_competition_view(self):
        kwargs = {'competition_slug': 'f1'}
        self._test_driver_record_view('dr27-competition', kwargs)

    def test_driver_records_global_view(self):
        kwargs = {}
        self._GET_request('dr27-global-index')
        self._GET_request('dr27-global-driver')
        self._GET_request('dr27-global-driver-olympic')
        self._test_driver_record_view('dr27-global', kwargs)

    def test_driver_records_redir(self):
        kwargs = {'record': 'POLE'}
        response = self.client.post(reverse('dr27-driver-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)
        kwargs['competition'] = 'f1'
        response = self.client.post(reverse('dr27-driver-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)
        kwargs['year'] = '2016'
        response = self.client.post(reverse('dr27-driver-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)

    def test_profiles_view(self):

        self._GET_request('dr27-profile-view', kwargs={'driver_id': 1})
        self._GET_request('dr27-profile-team-view', kwargs={'team_id': 1})

    def _test_team_records_view(self, base_path, kwargs):
        self._GET_request(base_path+'-team-record-index', kwargs=kwargs)
        kwargs['record'] = 'POLE'
        self._GET_request(base_path+'-team-record', kwargs=kwargs)
        self._GET_request(base_path+'-team-record-races', kwargs=kwargs)
        self._GET_request(base_path+'-team-record-doubles', kwargs=kwargs)
        self._GET_request(base_path+'-team-streak', kwargs=kwargs)
        self._GET_request(base_path+'-team-top-streak', kwargs=kwargs)

        if base_path == 'dr27-competition' or base_path == 'dr27-global':
            self._GET_request(base_path+'-team-seasons', kwargs=kwargs)

        kwargs['record'] = 'FFF'
        self._GET_request(base_path+'-team-record', kwargs=kwargs, code=404)

    def test_team_records_redir(self):
        kwargs = {'record': 'POLE'}
        response = self.client.post(reverse('dr27-team-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)
        kwargs['competition'] = 'f1'
        response = self.client.post(reverse('dr27-team-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)
        kwargs['year'] = '2016'
        response = self.client.post(reverse('dr27-team-record-redir'), data=kwargs)
        self.assertEqual(response.status_code, 302)



    def test_team_records_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016}
        self._test_team_records_view('dr27-season', kwargs)

    def test_team_records_competition_view(self):
        kwargs = {'competition_slug': 'f1'}
        self._test_team_records_view('dr27-competition', kwargs)
        
    def test_team_records_global_view(self):
        kwargs = {}
        self._GET_request('dr27-global-team')
        self._GET_request('dr27-global-driver-olympic')
        self._test_team_records_view('dr27-global', kwargs)

    def test_contender_season_points(self):
        driver = Driver.objects.get(pk=1)
        season = Season.objects.get(pk=1)
        contender_season = ContenderSeason(driver=driver, season=season)

        punctuation_config_a = get_punctuation_config('F1-25')
        contender_season_points_a = contender_season.get_points(punctuation_config=punctuation_config_a)
        punctuation_config_b = get_punctuation_config('F1-10+6')
        contender_season_points_b = contender_season.get_points(punctuation_config=punctuation_config_b)
        self.assertGreater(contender_season_points_a, contender_season_points_b)

    def test_result_tuple(self):
        seat = Seat.objects.get(pk=1)
        self.assertIsNotNone(get_results_tuples(seat=seat))

    def _check_get_changelist(self, ma):
        request = get_request()
        self.assertTrue(ma.get_changelist(request=request))

    def test_season_admin(self):
        ma = SeasonAdmin(Season, self.site)
        self._check_get_changelist(ma)
        self.assertTrue(ma.get_form(request=None, obj=None))
        self.assertIsInstance(ma.get_season_copy(copy_id=1), dict)

        request = get_request()
        season = Season.objects.get(pk=1)
        season_form = ma.get_form(request=request, obj=season)
        self.assertTrue(ma.print_copy_season(obj=season))
        self.assertIsNotNone(SeasonAdminForm(season_form))

    def _test_copy_url(self, COPY_URL, method_to_copy, data=None):
        season = Season.objects.get(pk=1)
        if data:
            request = self.factory.post(COPY_URL, data)
        else:
            request = self.factory.get(COPY_URL)
        ma = SeasonAdmin(Season, self.site)
        getattr(ma, method_to_copy)(request, season.pk)

    def _test_copy_items(self, COPY_URL, method_to_copy, new_season, items):
        self._test_copy_url(COPY_URL, method_to_copy)

        post_destiny = {
            'season_destiny': new_season.pk,
            'items': items,
            '_selector': True
        }

        self._test_copy_url(COPY_URL, method_to_copy, post_destiny)

        del post_destiny['_selector']
        post_destiny['_confirm'] = True

        self._test_copy_url(COPY_URL, method_to_copy, post_destiny)

    def test_season_copy_items(self):
        Season.objects.create(
            competition_id=1,
            year=2099,
            punctuation='F1-25',
            rounds=30
        )
        # todo check rounds
        new_season = Season.objects.get(competition_id=1, year=2099)

        season = Season.objects.get(pk=1)

        # races
        COPY_RACES_URL = reverse('admin:dr27-copy-races', kwargs={'pk': season.pk})
        races = [race.pk for race in season.races.all()]
        self._test_copy_items(COPY_RACES_URL, 'get_copy_races', new_season, races)

        ma = SeasonAdmin(Season, self.site)
        self.assertIn(COPY_RACES_URL, ma.print_copy_races(season))

    def test_driver_admin(self):
        ma = DriverAdmin(Driver, self.site)
        self._check_get_changelist(ma)

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

    def _test_season_formset(self, child_model, formset, fields):
        inline_formset = inlineformset_factory(Season, child_model, formset=formset,
                                               fields=fields,
                                               form=AlwaysChangedModelForm, can_delete=True)
        return inline_formset

    def _test_season_formset_copy(self, child_model, formset, fields, data=None):
        inline_formset = self._test_season_formset(child_model, formset, fields)
        # inline_formset.request = self.factory.request(QUERY_STRING='copy=1')
        related_formset = inline_formset(data)
        # self.assertTrue(related_formset.get_copy(copy_id=1))
        # self.assertFalse(related_formset.is_empty_form())
        self.assertFalse(related_formset.has_changed())
        return related_formset

    def test_race_formset(self):
        self._test_season_formset_copy(Race, RaceFormSet,
                                       ('round', 'grand_prix', 'circuit', 'date', 'alter_punctuation'))

    def test_race_admin(self):
        ma = RaceAdmin(Race, self.site)
        self._check_get_changelist(ma)
        race = Race.objects.get(pk=1)
        self.assertEquals(ma.print_pole(race), str(race.pole.driver))
        self.assertEquals(ma.print_winner(race), str(race.winner.driver))
        self.assertEquals(ma.print_fastest(race), str(race.fastest.driver))
        self.assertEquals(ma.clean_position('1'), 1)

    def _check_formfield_for_foreignkey(self, ma, request_obj, dbfield):
        request = get_request()
        request._obj_ = request_obj
        self.assertIsNotNone(ma.formfield_for_foreignkey(dbfield, request=request))

    def test_race_inline(self):
        race = Race.objects.get(pk=1)
        race_ma = RaceInline(SeasonAdmin, self.site)
        request = get_request()
        # self.assertIsNotNone(race_ma.get_formset())
        season = race.season
        self._check_formfield_for_foreignkey(race_ma, request_obj=season, dbfield=Race.grand_prix.field)

    # Currently not exists race with no results
    # def test_race_with_no_results(self):
    #     ma = RaceAdmin(Race, self.site)
    #     race = Race.objects.get(pk=20)  # No results
    #     self.assertIsNone(ma.print_pole(race))
    #     self.assertIsNone(ma.print_winner(race))
    #     self.assertIsNone(ma.print_fastest(race))

    def test_team_season_inline_admin(self):
        ma = TeamSeasonInline(SeasonAdmin, self.site)
        season = Season.objects.get(pk=1)
        self._check_formfield_for_foreignkey(ma, request_obj=season, dbfield=TeamSeason.team.field)
        team = Team.objects.get(pk=1)
        self._check_formfield_for_foreignkey(ma, request_obj=team, dbfield=TeamSeason.team.field)

    def test_related_competition_admin(self):
        race = Race.objects.get(pk=1)
        related_competition = RelatedCompetitionAdmin()
        # maybe exception
        self.assertIsNone(related_competition.print_competitions(race))


class DR27Api(APITestCase):
    fixtures = get_fixtures_test()

    def _GET_request(self, reverse_url, kwargs=None, code=200):
        request_url = reverse(reverse_url, kwargs=kwargs)
        response = self.client.get(request_url, format='json')
        self.assertEqual(response.status_code, code)

    def test_api_circuit(self):
        self._GET_request('circuit-list')

    def test_api_competition(self):
        self._GET_request('competition-list')
        self._GET_request('competition-detail', kwargs={'pk': 1})
        self._GET_request('competition-next-race', kwargs={'pk': 1})
        self._GET_request('competition-teams', kwargs={'pk': 1})

    def test_api_driver(self):
        self._GET_request('driver-list')
        self._GET_request('driver-detail', kwargs={'pk': 1})
        self._GET_request('driver-seats', kwargs={'pk': 1})

    def test_api_grand_prix(self):
        self._GET_request('grandprix-list')
        self._GET_request('grandprix-detail', kwargs={'pk': 1})

    def test_api_race(self):
        self._GET_request('race-list')
        self._GET_request('race-detail', kwargs={'pk': 1})
        self._GET_request('race-no-start-seats', kwargs={'pk': 1})
        self._GET_request('race-results', kwargs={'pk': 1})
        self._GET_request('race-seats', kwargs={'pk': 1})

    def test_api_result(self):
        self._GET_request('result-list')
        self._GET_request('result-detail', kwargs={'pk': 1})

    def test_api_season(self):
        self._GET_request('season-list')
        self._GET_request('season-detail', kwargs={'pk': 1})
        self._GET_request('season-next-race', kwargs={'pk': 1})
        self._GET_request('season-no-seats', kwargs={'pk': 1})
        self._GET_request('season-races', kwargs={'pk': 1})
        self._GET_request('season-seats', kwargs={'pk': 1})
        self._GET_request('season-standings', kwargs={'pk': 1})
        self._GET_request('season-standings-team', kwargs={'pk': 1})
        self._GET_request('season-teams', kwargs={'pk': 1})
        self._GET_request('season-title', kwargs={'pk': 1})

    def test_api_seat(self):
        self._GET_request('seat-list')
        self._GET_request('seat-detail', kwargs={'pk': 1})
        self._GET_request('seat-periods', kwargs={'pk': 1})
        self._GET_request('seatperiod-list')
        self._GET_request('seatperiod-detail', kwargs={'pk': 1})

    def test_api_team(self):
        self._GET_request('team-list')
        self._GET_request('team-detail', kwargs={'pk': 1})
