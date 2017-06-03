# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .common import CommonResultTestCase
from ..models import TeamSeason, Seat, CompetitionTeam


class SeasonTestCase(TestCase, CommonResultTestCase):
    def test_season_unicode(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        year = season.year
        expected_season = '{competition}/{year}'.format(competition=competition, year=year)
        self.assertEquals(str(season), expected_season)

    def test_season_scoring(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertIsInstance(season.get_punctuation_config(), dict)
        season.punctuation = 'BLABLABLA'
        self.assertIsNone(season.save())
        self.assertIsNone(season.get_punctuation_config())

    def test_season_has_champion(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertFalse(season.has_champion())

    def test_season_pending_races(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertIsInstance(season.pending_races(), int)

    def test_season_pending_points(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertIsInstance(season.pending_points(), (int, float))

    def test_season_contenders(self):
        seat_a = self.get_test_seat()
        seat_b = self.get_test_seat_b(seat_a)
        team = seat_a.team
        competition = self.get_test_competition_a()
        self.assertTrue(CompetitionTeam.objects.create(competition=competition, team=team))
        # season = self.get_test_season(competition)
        race = self.get_test_race(competition, round=1)
        season = race.season
        result_a = self.get_test_result(seat=seat_a, race=race, qualifying=1, finish=2)
        result_b = self.get_test_result(seat=seat_b, race=race, qualifying=4, finish=7)
        self.assertEquals(season.drivers.count(), 2)
