# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonResultTestCase
from ..models import Result, TeamSeason

class ResultTestCase(TestCase, CommonResultTestCase):
    def test_result_shorcuts(self):
        result = self.get_test_result()
        self.assertEquals(result.driver, result.seat.contender.driver)
        self.assertEquals(result.team, result.seat.team)

    def test_result_fastest_unique(self):
        result = self.get_test_result()
        result.fastest_lap = True
        self.assertIsNone(result.save())
        seat_a = result.seat
        race = result.race
        # create result_b
        seat_b = self.get_test_seat_b(seat_a=seat_a)
        result_b = self.get_test_result(seat=seat_b, race=race)
        result_b.fastest_lap = True
        self.assertIsNone(result_b.save())
        # Although both results have fastest_lap=True, only the first is saved.
        self.assertEquals(Result.objects.filter(race=race, fastest_lap=True).count(), 1)
        self.assertEquals(Result.objects.get(race=race, seat=seat_a).fastest_lap, True)
        self.assertEquals(Result.objects.get(race=race, seat=seat_b).fastest_lap, False)

    def test_result_points(self):
        result = self.get_test_result()
        seat = result.seat
        race = result.race
        season = race.season
        season.punctuation = 'F1-25'
        self.assertIsNone(season.save())

        result.qualifying = 2
        result.finish = 2
        self.assertIsNone(result.save())

        # result.finish = 2 = ?? points
        self.assertGreater(result.points, 0)
        team_season = TeamSeason.objects.get(team=seat.team, season=season)
        self.assertGreater(team_season.get_points(), 0)
        race_points = result.points

        # change scoring to add fastest_lap point
        scoring = season.get_scoring()
        scoring['fastest_lap'] = 1
        # result + fastest_lap
        result.fastest_lap = True
        self.assertIsNone(result.save())
        # result.points is greater than before
        self.assertGreater(result.points, race_points)
        self.assertEquals(race.fastest, result.seat)

    def test_result_team_exception(self):
        self.get_test_result(raise_team_exception=True)