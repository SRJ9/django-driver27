# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .common import CommonResultTestCase
from ..models import TeamSeason, Seat, CompetitionTeam


class SeasonTestCase(TestCase, CommonResultTestCase):
    def test_season_unicode(self):
        season = self.get_test_season()
        year = season.year
        expected_season = '{competition}/{year}'.format(competition=season.competition, year=year)
        self.assertEquals(str(season), expected_season)

    def test_season_scoring(self):
        season = self.get_test_season()
        self.assertIsInstance(season.get_punctuation_config(), dict)
        season.punctuation = 'BLABLABLA'
        self.assertIsNone(season.save())
        self.assertIsNone(season.get_punctuation_config())

    def test_season_has_champion(self):
        season = self.get_test_season()
        self.assertFalse(season.has_champion())

    def test_season_pending_races(self):
        season = self.get_test_season()
        self.assertIsInstance(season.pending_races(), int)

    def test_season_pending_points(self):
        season = self.get_test_season()
        self.assertIsInstance(season.pending_points(), (int, float))

    def test_season_contenders(self):
        seat_a = self.get_test_seat()
        seat_b = self.get_test_seat_teammate(seat_a)
        team = seat_a.team
        competition = self.get_test_competition()
        self.assertTrue(CompetitionTeam.objects.create(competition=competition, team=team))
        # season = self.get_test_season(competition)
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season, round=1)
        result_a = self.get_test_result(seat=seat_a, race=race, qualifying=1, finish=2)
        result_b = self.get_test_result(seat=seat_b, race=race, qualifying=4, finish=7)
        self.assertEquals(season.drivers.count(), 2)
