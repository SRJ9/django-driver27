# -*- coding: utf-8 -*-
import sys

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
        self.assertTrue(model.objects.create(**kwargs))
        return model.objects.get(**kwargs)


class CommonDriverTestCase(object):
    def set_test_driver(self, **kwargs):
        self.assertTrue(Driver.objects.create(year_of_birth=1985, country='ES', **kwargs))
        return Driver.objects.get(**kwargs)

    def get_test_driver_a(self):
        test_driver_args = {'last_name': 'García', 'first_name': 'Juan'}
        return self.set_test_driver(**test_driver_args)

    def get_test_driver_b(self):
        test_driver_args = {'last_name': 'López', 'first_name': 'Jaime'}
        return self.set_test_driver(**test_driver_args)


class CommonCompetitionTestCase(CommonCreateTestCase):
    def set_test_competition(self, **kwargs):
        return self.set_test_create(model=Competition, **kwargs)

    def get_test_competition_a(self):
        test_competition_args = {'name': 'Competición A', 'full_name': 'Competición ABC'}
        return self.set_test_competition(**test_competition_args)

    def get_test_competition_b(self):
        test_competition_args = {'name': 'Competición B', 'full_name': 'Competición BDF'}
        return self.set_test_competition(**test_competition_args)


class CommonTeamTestCase(CommonCreateTestCase):
    def set_test_team(self, **kwargs):
        return self.set_test_create(model=Team, **kwargs)

    def get_test_team(self):
        team_args = {'name': 'Escudería Tec Auto', 'full_name': 'Escudería Tec Auto', 'country': 'ES'}
        return self.set_test_team(**team_args)

    def get_test_team_b(self):
        team_args = {'name': 'D27R', 'full_name': 'Driver 27 Racing Team', 'country': 'ES'}
        return self.set_test_team(**team_args)


class CommonSeasonTestCase(CommonCompetitionTestCase):
    def set_test_season(self, **kwargs):
        return self.set_test_create(model=Season, **kwargs)

    def get_test_season(self, competition, year=2016):
        season_args = {'year': year, 'competition': competition, 'punctuation': 'F1-25', 'rounds': 10}
        return self.set_test_season(**season_args)


class CommonTeamSeasonTestCase(CommonTeamTestCase, CommonSeasonTestCase):
    pass


class CommonSeatTestCase(CommonDriverTestCase, CommonTeamTestCase):
    def set_test_seat(self, **kwargs):
        self.assertTrue(Seat.objects.create(**kwargs))
        seat = Seat.objects.get(**kwargs)
        return seat

    def get_test_seat(self):
        driver = self.get_test_driver_a()
        team = self.get_test_team()
        seat_args = {'driver': driver, 'team': team}
        return self.set_test_seat(**seat_args)

    def get_test_seat_b(self, seat_a):
        driver = self.get_test_driver_b()
        team = seat_a.team
        seat_args = {'driver': driver, 'team': team}
        return self.set_test_seat(**seat_args)

    def get_test_seat_c(self, seat_a):
        driver = seat_a.driver
        team = self.get_test_team_b()
        seat_args = {'driver': driver, 'team': team}
        return self.set_test_seat(**seat_args)


class CommonRaceTestCase(CommonSeasonTestCase):
    def get_test_circuit(self):
        circuit_args = {"name": "Autódromo de Jacarepaguá", "city": "Jacarepaguá"}
        self.assertTrue(Circuit.objects.create(country='BR', opened_in=1978, **circuit_args))
        circuit = Circuit.objects.get(**circuit_args)
        return circuit

    def get_test_grandprix(self):
        circuit = self.get_test_circuit()
        grandprix_args = {'name': 'Grande Prêmio do Brasil'}
        self.assertTrue(GrandPrix.objects.create(
            default_circuit=circuit, country='BR', first_held=1972, **grandprix_args))
        return GrandPrix.objects.get(**grandprix_args)

    def get_test_race(self, competition=None, season=None, round=1):
        if season is None:
            if competition is None:
                competition = self.get_test_competition_a()
            season = self.get_test_season(competition=competition)
        race_args = {
            'round': round,
            'season': season,
            'date': None,
            'alter_punctuation': None
        }
        # race without grandprix
        self.assertTrue(Race.objects.create(**race_args))
        race = Race.objects.get(season=season, round=1)
        return race

class CommonResultTestCase(CommonSeatTestCase, CommonRaceTestCase):
    def set_test_result(self, *args, **kwargs):
        self.assertTrue(Result.objects.create(**kwargs))
        result = Result.objects.get(**{'seat': kwargs['seat'], 'race': kwargs['race']})
        return result

    def get_result_seat(self, seat):
        if not seat:
            seat = self.get_test_seat()
        return seat

    def get_result_race(self, race, competition=None):
        if not race:
            race = self.get_test_race(competition=competition)
        return race

    def get_test_result(self, seat=None, race=None, qualifying=None, finish=None,
                        raise_seat_exception=False, raise_team_exception=False):
        # when raise_team_exception, the team-season will not be created
        # raise a exception, because the team is invalid in that season
        seat = self.get_result_seat(seat)  # if seat is None, get default seat
        race = self.get_result_race(race=race)  # If Race is None, get default race
        result_args = {
            'seat': seat,
            'race': race,
            'qualifying': qualifying,
            'finish': finish,
            'fastest_lap': False,
            'retired': False,
            'wildcard': False,
            'comment': None
        }

        if not raise_team_exception:
            if race.season.competition not in seat.team.competitions.all():
                self.assertTrue(CompetitionTeam.objects.create(competition=race.season.competition, team=seat.team))
        return self.set_test_result(**result_args)
