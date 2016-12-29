# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonResultTestCase
from ..models import Result, Seat, TeamSeason, ContenderSeason

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
        self.assertEquals(Result.objects.get(race=race, seat=seat_a).fastest_lap, True)
        # create result_b
        seat_b = self.get_test_seat_b(seat_a=seat_a)
        result_b = self.get_test_result(seat=seat_b, race=race)
        result_b.fastest_lap = True
        self.assertIsNone(result_b.save())
        # Although both results have fastest_lap=True, only the last is saved.
        self.assertEquals(Result.objects.filter(race=race, fastest_lap=True).count(), 1)
        self.assertEquals(Result.objects.get(race=race, seat=seat_a).fastest_lap, False)
        self.assertEquals(Result.objects.get(race=race, seat=seat_b).fastest_lap, True)

    def test_result_points(self):
        result = self.get_test_result()
        seat = result.seat
        race = result.race
        season = race.season
        # season.punctuation = 'F1-25'
        # self.assertIsNone(season.save())

        result.qualifying = 2
        result.finish = 2
        self.assertIsNone(result.save())

        # result.finish = 2 = ?? points
        self.assertGreater(result.points, 0)
        team_season = TeamSeason.objects.get(team=seat.team, season=season)
        self.assertGreater(team_season.get_points(), 0)
        race_points = result.points

        # change scoring to add fastest_lap point
        result.fastest_lap = True
        self.assertIsNone(result.save())

        # modify scoring to check if fastest_lap scoring is counted
        scoring = season.get_scoring()
        scoring['fastest_lap'] = 1
        with self.settings(DR27_CONFIG={'PUNCTUATION': {'F1-25': scoring}}):
            # result.points is greater than before
            self.assertGreater(result.points, race_points)  # No working currently
        self.assertEquals(race.fastest, result.seat)

    def test_result_seat_exception(self):
        self.get_test_result(raise_seat_exception=True)

    def test_result_team_exception(self):
        self.get_test_result(raise_team_exception=True)

    def test_rank(self):
        result_a = self.get_test_result(qualifying=2, finish=1)
        seat_a = result_a.seat
        race = result_a.race
        # set season
        season = race.season
        # season.punctuation = 'F1-25'
        # self.assertIsNone(season.save())

        seat_b = self.get_test_seat_b(seat_a=seat_a)
        result_b = self.get_test_result(seat=seat_b, race=race, qualifying=1, finish=3)

        # pole
        self.assertEquals(race.pole, seat_b)
        # winner
        self.assertEquals(race.winner, seat_a)

        # season contender = 2
        self.assertEquals(len(season.contenders()), 2)
        self.assertEquals(len(season.points_rank()), 2)
        self.assertEquals(len(season.olympic_rank()), 2)
        self.assertEquals(len(season.team_points_rank()), 1) # seat a and seat b is in the same team
        self.assertEquals(season.leader[1], seat_a.contender.driver) # seat a.driver is the winner, the leader
        self.assertEquals(season.team_leader[1], seat_a.team)

        # contenderseason.get_points
        contender_a = seat_a.contender
        contender_season = ContenderSeason(contender=contender_a, season=season)
        self.assertGreater(contender_season.get_points(), 0)
        self.assertGreater(contender_season.get_points(1), 0)
