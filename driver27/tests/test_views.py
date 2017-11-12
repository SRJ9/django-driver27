from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, Client, RequestFactory

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from ..models import Season, Driver, Team, Competition, Circuit, get_tuples_from_results
from ..models import GrandPrix, Race, Seat, TeamSeason, ContenderSeason
from ..admin import SeasonAdmin, SeasonAdminForm, DriverAdmin, TeamAdmin
from ..admin import CompetitionAdmin, CircuitAdmin, GrandPrixAdmin
from ..admin import RaceAdmin, RelatedCompetitionAdmin
from ..admin import RaceInline, ResultInline, SeatInline
from ..admin.forms import RaceAdminForm
from ..admin.formsets import RaceFormSet
from ..admin.common import get_circuit_id_from_gp, GrandPrixWidget
from ..punctuation import get_punctuation_config
from rest_framework.test import APITestCase
from ..common import DRIVER27_NAMESPACE, DRIVER27_API_NAMESPACE
from django import forms

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

    def _GET_request(self, reverse_url, kwargs=None, data=None, code=200):
        # Issue a GET request.
        reverse_url = DRIVER27_NAMESPACE+':'+reverse_url
        the_reverse = reverse(reverse_url, kwargs=kwargs)
        response = self.client.get(the_reverse, data=data)
        # Check that the response is 302 OK.
        self.assertEqual(response.status_code, code)

    # def test_competition_list(self):
    #     self._GET_request('competition:list')

    def _test_competition_view(self):
        kwargs = {'competition_slug': 'f1'}
        self._GET_request('competition:view', kwargs=kwargs)
        self._GET_request('competition:driver-olympic', kwargs=kwargs)
        self._GET_request('competition:driver-comeback', kwargs=kwargs)
        self._GET_request('competition:driver-record-index', kwargs=kwargs)
        self._GET_request('competition:team-olympic', kwargs=kwargs)
        self._GET_request('competition:driver-seasons-rank', kwargs=kwargs)
        self._GET_request('competition:team-seasons-rank', kwargs=kwargs)
        self._GET_request('competition:driver-record-index', kwargs=kwargs)
        self._GET_request('competition:view', kwargs={'competition_slug': 'f19'}, code=404)

    def _test_season_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016}
        self._GET_request('season:view', kwargs=kwargs)
        self._GET_request('season:race-list', kwargs=kwargs)
        race_kw = {'race_id': 1}
        race_kw.update(kwargs)
        self._GET_request('season:race-view', kwargs=race_kw)
        self._GET_request('season:driver', kwargs=kwargs)
        self._GET_request('season:driver-olympic', kwargs=kwargs)
        self._GET_request('season:driver-comeback', kwargs=kwargs)
        self._GET_request('season:driver-record-index', kwargs=kwargs)
        self._GET_request('season:team', kwargs=kwargs)
        self._GET_request('season:team-olympic', kwargs=kwargs)
        self._GET_request('season:team-record-index', kwargs=kwargs)
        self._GET_request('season:race-list', kwargs=kwargs)

        kwargs = {'competition_slug': 'f19', 'year': 2006}
        self._GET_request('season:view', kwargs=kwargs, code=404)

    def test_ajax_standing(self, model='driver', default_code=200):
        URL = 'dr27-ajax:standing'
        data = {'model': model}
        self._GET_request(URL, data=data, code=default_code)
        data['competition_slug'] = 'f1'
        self._GET_request(URL, data=data, code=default_code)
        data['year'] = 2016
        self._GET_request(URL, data=data, code=default_code)
        data['olympic'] = True
        self._GET_request(URL, data=data, code=default_code)

    def test_ajax_standing_team(self):
        self.test_ajax_standing(model='team')

    def test_ajax_standing_404_model(self):
        self.test_ajax_standing(model='else', default_code=404)

    def test_ajax_stats(self, model='driver', default_code=200):
        URL = 'dr27-ajax:stats'
        data = {'model': model}
        self._GET_request(URL, data=data, code=default_code)
        data['competition_slug'] = 'f1'
        self._GET_request(URL, data=data, code=default_code)
        data['year'] = 2016
        self._GET_request(URL, data=data, code=default_code)
        data['record'] = 'POLE'
        self._GET_request(URL, data=data, code=default_code)
        for opt in [None, 'streak', 'seasons', 'streak_top', 'streak_actives', 'streak_top_actives']:
            data['rank_opt'] = opt
            self._GET_request(URL, data=data, code=default_code)
        data['record'] = 'FFF'
        self._GET_request(URL, data=data, code=404)

    def test_ajax_stats_team(self):
        self.test_ajax_stats(model='team')

    def test_ajax_stats_404_model(self):
        self.test_ajax_stats(model='else', default_code=404)

    def test_race_view(self):
        kwargs = {'competition_slug': 'f1', 'year': 2016, 'race_id': 1}
        self._GET_request('season:race-view', kwargs=kwargs)
        kwargs['race_id'] = 200
        self._GET_request('season:race-view', kwargs=kwargs, code=404)


    def test_driver_records_global_view(self):
        kwargs = {}
        self._GET_request('global:index')
        self._GET_request('global:driver')
        self._GET_request('global:driver-olympic')
        self._GET_request('global:driver-seasons-rank')
        self._GET_request('global:driver-comeback')
        self._GET_request('global:driver-record-index')
        self._test_competition_view()
        self._test_season_view()

    def test_profiles_view(self):

        self._GET_request('global:driver-profile', kwargs={'driver_id': 1})
        self._GET_request('global:team-profile', kwargs={'team_id': 1})

        
    def test_team_records_global_view(self):
        self._GET_request('global:team')
        self._GET_request('global:team-olympic')
        self._GET_request('global:team-seasons-rank')
        self._GET_request('global:team-record-index')

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
        results = seat.results.all()
        self.assertIsNotNone(get_tuples_from_results(results=results))

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

    def test_season_duplicate(self):
        season = Season.objects.last()
        COPY_SEASON_URL = reverse('admin:dr27-copy-season', kwargs={'pk': season.pk})
        request = self.factory.get(COPY_SEASON_URL)
        ma = SeasonAdmin(Season, self.site)
        getattr(ma, 'get_duplicate_season')(request, season.pk)

        request = self.factory.post(COPY_SEASON_URL, data={'year': season.year, '_selector': True})
        ma = SeasonAdmin(Season, self.site)
        getattr(ma, 'get_duplicate_season')(request, season.pk)

        NEW_SEASON_YEAR = 9999
        request = self.factory.post(COPY_SEASON_URL, data={'year': NEW_SEASON_YEAR, '_selector': True})
        ma = SeasonAdmin(Season, self.site)
        getattr(ma, 'get_duplicate_season')(request, season.pk)

        self.assertTrue(Season.objects.get(competition=season.competition, year=NEW_SEASON_YEAR))

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
                                               form=forms.ModelForm, can_delete=True)
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

    def test_result_inline(self):
        race = Race.objects.get(pk=1)
        result = race.results.filter(points__gt=0).first()
        self.assertEqual(ResultInline(RaceAdmin, self.site).points(result), result.points)

        result = race.results.filter(points=0).first()
        self.assertFalse(ResultInline(RaceAdmin, self.site).points(result))

    def test_race_admin_fastest_car(self):
        race = Race.objects.get(pk=1)
        self.assertTrue(RaceAdminForm(instance=race))

    def test_seat_inline(self):
        driver = Driver.objects.get(pk=1)
        seat = driver.seats.first()
        link = str(reverse('admin:driver27_seat_change', args=[seat.pk]))
        self.assertIn(link, SeatInline(DriverAdmin, self.site).edit(seat))

    # Currently not exists race with no results
    # def test_race_with_no_results(self):
    #     ma = RaceAdmin(Race, self.site)
    #     race = Race.objects.get(pk=20)  # No results
    #     self.assertIsNone(ma.print_pole(race))
    #     self.assertIsNone(ma.print_winner(race))
    #     self.assertIsNone(ma.print_fastest(race))


    def test_related_competition_admin(self):
        race = Race.objects.get(pk=1)
        related_competition = RelatedCompetitionAdmin()
        # maybe exception
        self.assertIsNone(related_competition.print_competitions(race))

    def test_circuit_widget(self):
        grand_prix = GrandPrix.objects.filter(default_circuit__isnull=False).first()
        self.assertEqual(get_circuit_id_from_gp(grand_prix.pk), grand_prix.default_circuit.pk)





class DR27Api(APITestCase):
    fixtures = get_fixtures_test()

    def _GET_request(self, reverse_url, kwargs=None, code=200):
        reverse_url = ':'.join([DRIVER27_NAMESPACE, DRIVER27_API_NAMESPACE, reverse_url])
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
        self._GET_request('race-no-seats', kwargs={'pk': 1})
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
