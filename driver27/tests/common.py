# -*- coding: utf-8 -*-
import sys
import six
from django.core.exceptions import ValidationError
from ..models import Driver, Competition, Team, Season, Circuit
from ..models import TeamSeason, Seat, GrandPrix, Race, Result, ContenderSeason, CompetitionTeam


def retro_encode(text):
    if sys.version_info < (3, 0):
        try:
            return text.encode('utf-8')
        except UnicodeDecodeError:
            return text
    else:
        return text


class CommonCreateTestCase(object):
    def set_test_create(self, model, **kwargs):
        return model.objects.create(**kwargs)


class CommonDriverTestCase(CommonCreateTestCase):
    def get_test_driver(self, **kwargs):
        defaults = {
            'last_name': u'García',
            'first_name': u'Juan'
        }
        defaults.update(**kwargs)
        return self.set_test_create(model=Driver, **defaults)

    def get_test_driver_2(self):
        kwargs = {
            'last_name': u'López',
            'first_name': u'Jaime'
        }
        return self.get_test_driver(**kwargs)


class CommonCompetitionTestCase(CommonCreateTestCase):
    def get_test_competition(self, **kwargs):
        defaults = {
            'name': u'Competición A',
            'full_name': u'Competición ABC'
        }
        defaults.update(**kwargs)
        return self.set_test_create(model=Competition, **defaults)

    def get_test_competition_2(self):
        kwargs = {
            'name': u'Competición B',
            'full_name': u'Competición BDF'
        }
        return self.get_test_competition(**kwargs)


class CommonTeamTestCase(CommonCompetitionTestCase):
    def get_test_team(self, **kwargs):
        defaults = {
            'name': u'Escudería Tec Auto',
            'full_name': u'Escudería Tec Auto'
        }
        defaults.update(**kwargs)
        return self.set_test_create(model=Team, **defaults)

    def get_test_team_2(self):
        kwargs = {
            'name': u'D27R',
            'full_name': u'Driver 27 Racing Team'
        }
        return self.get_test_team(**kwargs)

    def get_test_competition_team(self, **kwargs):
        defaults = {}
        defaults.update(**kwargs)
        if 'competition' not in defaults:
            defaults['competition'] = self.get_test_competition()
        if 'team' not in defaults:
            defaults['team'] = self.get_test_team()
        return self.set_test_create(model=CompetitionTeam, **defaults)


class CommonSeasonTestCase(CommonCompetitionTestCase):
    def get_test_season(self, **kwargs):
        defaults = {
            'year': 2016,
            'punctuation': u'F1-25'
        }
        defaults.update(**kwargs)
        if 'competition' not in defaults:
            defaults['competition'] = self.get_test_competition()
        return self.set_test_create(model=Season, **defaults)


class CommonTeamSeasonTestCase(CommonTeamTestCase, CommonSeasonTestCase):
    pass


class CommonSeatTestCase(CommonDriverTestCase, CommonTeamTestCase):
    def get_test_seat(self, **kwargs):
        defaults = {}
        defaults.update(**kwargs)
        if 'driver' not in defaults:
            defaults['driver'] = self.get_test_driver()
        if 'team' not in defaults:
            defaults['team'] = self.get_test_team()
        return self.set_test_create(model=Seat, **defaults)

    def get_test_seat_teammate(self, seat_a):
        driver = self.get_test_driver_2()
        team = seat_a.team
        seat_args = {'driver': driver, 'team': team}
        return self.get_test_seat(**seat_args)

    def get_test_seat_same_driver_other_team(self, seat_a):
        driver = seat_a.driver
        team = self.get_test_team_2()
        seat_args = {'driver': driver, 'team': team}
        return self.get_test_seat(**seat_args)


class CommonRaceTestCase(CommonSeasonTestCase):
    def get_test_race(self, **kwargs):
        defaults = {'round': 1}
        defaults.update(**kwargs)
        if 'season' not in defaults:
            defaults['season'] = self.get_test_season()
        return self.set_test_create(model=Race, **defaults)

    def get_test_circuit(self, **kwargs):
        defaults = {
            'name': u'Autódromo de Jacarepaguá',
            'city': u'Jacarepaguá',
            'opened_in': 1978
        }
        defaults.update(**kwargs)
        return self.set_test_create(model=Circuit, **defaults)

    def get_test_grandprix(self, **kwargs):
        defaults = {'name': u'Grande Prêmio do Brasil'}
        defaults.update(**kwargs)
        return self.set_test_create(model=GrandPrix, **defaults)


class CommonResultTestCase(CommonSeatTestCase, CommonRaceTestCase):
    def get_test_result(self, **kwargs):
        defaults = {}
        defaults.update(**kwargs)
        if 'seat' not in defaults:
            defaults['seat'] = self.get_test_seat()
        if 'race' not in defaults:
            defaults['race'] = self.get_test_race()
        return self.set_test_create(model=Result, **defaults)