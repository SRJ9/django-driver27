# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonResultTestCase
from ..models import Result, Seat, TeamSeason, ContenderSeason, SeatPeriod, CompetitionTeam
from django.core.exceptions import ValidationError


class ResultTestCase(TestCase, CommonResultTestCase):
    def test_result_shorcuts(self):
        result = self.get_test_result()
        self.assertEquals(result.driver, result.seat.driver)
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
        team_season, created = TeamSeason.objects.get_or_create(team=seat.team, season=season)
        self.assertGreater(team_season.get_points(), 0)
        race_points = result.points

        # change scoring to add fastest_lap point
        result.fastest_lap = True
        self.assertIsNone(result.save())

        # modify scoring to check if fastest_lap scoring is counted
        punctuation_config = season.get_punctuation_config()
        punctuation_config['fastest_lap'] = 1
        self.assertGreater(result.points_calculator(punctuation_config), race_points)
        self.assertEquals(race.fastest, result.seat)

    def test_result_str(self):
        result = self.get_test_result()
        result.finish = 14
        result_str = '{seat} ({race})'.format(seat=result.seat, race=result.race)
        result_str_checkered_flag = result_str + ' - {finish}º'.format(finish=result.finish)
        self.assertEqual(str(result), result_str_checkered_flag)

        result_str_out = result_str + ' - DNF'
        result.finish = None
        self.assertEqual(str(result), result_str_out)

    def test_result_seat_exception(self):
        self.get_test_result(raise_seat_exception=True)

    def test_rank(self):
        result_a = self.get_test_result(qualifying=2, finish=1)
        seat_a = result_a.seat
        race = result_a.race
        # set season
        season = race.season
        # season.punctuation = 'F1-25'
        # self.assertIsNone(season.save())

        seat_b = self.get_test_seat_b(seat_a=seat_a)
        self.get_test_result(seat=seat_b, race=race, qualifying=1, finish=3)

        # pole
        self.assertEquals(race.pole, seat_b)
        # winner
        self.assertEquals(race.winner, seat_a)

        # season contender = 2
        self.assertEquals(season.drivers.count(), 2)
        self.assertEquals(len(season.points_rank()), 2)
        self.assertEquals(len(season.olympic_rank()), 2)
        self.assertEquals(len(season.team_points_rank()), 1) # seat a and seat b is in the same team
        self.assertEquals(season.leader[1], seat_a.driver) # seat a.driver is the winner, the leader
        self.assertEquals(season.team_leader[1], seat_a.team)

        # contenderseason.get_points
        driver_a = seat_a.driver
        contender_season = ContenderSeason(driver=driver_a, season=season)
        self.assertGreater(contender_season.get_points(), 0)
        self.assertGreater(contender_season.get_points(1), 0)

    def test_period_limitation(self):
        period_year = 2017
        seat_a = self.get_test_seat()
        self.assertTrue(SeatPeriod.objects.create(seat=seat_a, from_year=period_year, until_year=period_year))

        competition = self.get_test_competition_a()
        season_year = 2018
        season = self.get_test_season(competition=competition, year=season_year)
        race = self.get_test_race(season=season, round=1)
        self.assertRaises(ValidationError, self.get_test_result, **{'seat': seat_a, 'race': race,
                                                                    'qualifying': 2, 'finish': 2})

    def test_duplicate_driver(self):
        seat_a = self.get_test_seat()
        seat_b = self.get_test_seat_b(seat_a)
        seat_c = self.get_test_seat_c(seat_a)
        competition = self.get_test_competition_a()
        race = self.get_test_race(competition=competition, round=1)
        self.assertTrue(self.get_test_result(seat=seat_a, race=race, qualifying=1, finish=3))
        # seat_a and seat_c are the same driver in different teams. Only one seat by driver in race.
        self.assertRaises(ValidationError, self.get_test_result, **{'seat': seat_c, 'race': race,
                                                                    'qualifying': 2, 'finish': 2})
        self.assertEqual(race.results.count(), 1)

        # test swapfield. Seat_a loses the pole, Seat_b is poleman
        self.assertTrue(self.get_test_result(seat=seat_b, race=race, qualifying=1, finish=3))
        self.assertEqual(race.results.count(), 2)

        self.assertEqual(race.pole, seat_b)


