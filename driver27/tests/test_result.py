# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonResultTestCase
from ..models import Result, Seat, TeamSeason, ContenderSeason, SeatPeriod, CompetitionTeam
from ..records import get_record_config
from ..punctuation import get_punctuation_config
from django.core.exceptions import ValidationError

from collections import namedtuple


class ResultTestCase(TestCase, CommonResultTestCase):
    def _insert_massive_results(self, seat, season, results):
        for new_result in results:
            cur_race = self.get_test_race(season=season, round=new_result['round'])
            del new_result['round']
            self.get_test_result(race=cur_race, seat=seat, **new_result)

    def test_result_shorcuts(self):
        seat = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        self.get_test_competition_team(competition=competition, team=seat.team)
        result = self.get_test_result(seat=seat, race=race)
        self.assertEquals(result.driver, result.seat.driver)
        self.assertEquals(result.team, result.seat.team)

    def test_result_fastest_unique(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        self.get_test_competition_team(competition=competition, team=seat_a.team)
        result = self.get_test_result(seat=seat_a, race=race)
        result.fastest_lap = True
        self.assertIsNone(result.save())
        self.assertEquals(result.fastest_lap, True)
        # create result_b
        seat_b = self.get_test_seat_teammate(seat_a=seat_a)
        result_b = self.get_test_result(seat=seat_b, race=race)
        result_b.fastest_lap = True
        self.assertIsNone(result_b.save())
        # Although both results have fastest_lap=True, only the last is saved.
        self.assertEquals(Result.objects.filter(race=race, fastest_lap=True).count(), 1)
        self.assertEquals(Result.objects.get(race=race, seat=seat_a).fastest_lap, False)
        self.assertEquals(Result.objects.get(race=race, seat=seat_b).fastest_lap, True)

    def test_result_points(self):
        seat = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        self.get_test_competition_team(competition=competition, team=seat.team)
        result = self.get_test_result(seat=seat, race=race)

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
        seat = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        self.get_test_competition_team(competition=competition, team=seat.team)
        result = self.get_test_result(race=race, seat=seat)
        result.finish = 14
        result_str = '{seat} ({race})'.format(seat=result.seat, race=result.race)
        result_str_checkered_flag = result_str + ' - {finish}º'.format(finish=result.finish)
        self.assertEqual(str(result), result_str_checkered_flag)

        result_str_out = result_str + ' - DNF'
        result.finish = None
        self.assertEqual(str(result), result_str_out)

    def test_result_seat_exception(self):
        self.assertRaises(ValidationError, self.get_test_result)

    def test_streak_results(self):
        record_config = get_record_config('PODIUM').get('filter')
        seat = self.get_test_seat()
        driver = seat.driver
        competition_1 = self.get_test_competition()
        season_1 = self.get_test_season(competition=competition_1, rounds=8)
        self.get_test_competition_team(competition=competition_1, team=seat.team)

        results_1 = [
            {'round': 1, 'finish': 3, 'qualifying': 4},
            {'round': 2, 'finish': 2, 'qualifying': 13},
            {'round': 3, 'finish': 1, 'qualifying': 2},
            {'round': 4, 'finish': 1, 'qualifying': 1},
            {'round': 5, 'finish': 1, 'qualifying': 1},
            {'round': 6, 'finish': 8, 'qualifying': 5},
            {'round': 7, 'finish': 3, 'qualifying': 4},
            {'round': 8, 'finish': 3, 'qualifying': 3},
        ]

        self._insert_massive_results(seat=seat, season=season_1, results=results_1)

        self.assertEqual(driver.get_streak(**record_config), 2)
        self.assertEqual(driver.get_streak(max_streak=True, **record_config), 5)

        self.assertEqual(driver.get_points(season=season_1), 142)
        self.assertEqual(season_1.leader['points'], driver.get_points(season=season_1))
        self.assertTrue(season_1.has_champion())

        # season 2
        # same competition
        # streak continues
        # streak in season and streak global are diff
        year_2 = season_1.year+1
        season_2 = self.get_test_season(competition=competition_1, year=year_2)

        results_2 = [
            {'round': 1, 'finish': 3, 'qualifying': 4},
            {'round': 2, 'finish': 2, 'qualifying': 11},
            {'round': 3, 'finish': 1, 'qualifying': 20},
            {'round': 4, 'finish': 1, 'qualifying': 12}
        ]

        self._insert_massive_results(seat=seat, season=season_2, results=results_2)

        self.assertEqual(driver.get_streak(**record_config), 6)
        self.assertEqual(driver.get_season(season_2).get_streak(**record_config), 4)

        self.assertEqual(driver.get_points(season=season_2), 83)
        self.assertEqual(season_2.leader['points'], driver.get_points(season=season_2))

        # season 3
        # diff competition
        # streak continues
        # streak in season and streak in competition are the same but not streak global
        year_3 = season_2.year+1
        competition_2 = self.get_test_competition_2()
        self.get_test_competition_team(competition=competition_2, team=seat.team)
        season_3 = self.get_test_season(competition=competition_2, year=year_3)

        results_3 = [
            {'round': 1, 'finish': 1, 'qualifying': 2},
            {'round': 2, 'finish': 2, 'qualifying': 2},
            {'round': 3, 'finish': 3, 'qualifying': 2},
            {'round': 4, 'finish': 1, 'qualifying': 1},
            {'round': 5, 'finish': 1, 'qualifying': 1}
        ]

        self._insert_massive_results(seat=seat, season=season_3, results=results_3)

        self.assertEqual(driver.get_streak(**record_config), 11)
        self.assertEqual(driver.get_streak(result_filter={'competition': competition_2}, **record_config), 5)
        self.assertEqual(driver.get_season(season_3).get_streak(**record_config), 5)

        self.assertEqual(driver.get_points(season=season_3), 108)
        self.assertEqual(season_3.leader['points'], driver.get_points(season=season_3))


        # season 4
        # back to competition 1
        # streak global continues
        # but streak in competition continues from season 2 (skip season 3 - other competition)
        year_4 = season_3.year+1
        season_4 = self.get_test_season(competition=competition_1, year=year_4)

        results_4 = [
            {'round': 1, 'finish': 1, 'qualifying': 2},
            {'round': 2, 'finish': 1, 'qualifying': 2},
        ]

        self._insert_massive_results(seat=seat, season=season_4, results=results_4)

        self.assertEqual(driver.get_streak(**record_config), 13)
        self.assertEqual(driver.get_streak(result_filter={'competition': competition_1}, **record_config), 8)
        self.assertEqual(driver.get_season(season_4).get_streak(**record_config), 2)

        # bye streak
        # max_streak is past_streak and curr streak is 1

        results_bye_streak = [
            {'round': 3, 'finish': 5, 'qualifying': 3},
            {'round': 4, 'finish': 1, 'qualifying': 2},
        ]

        self._insert_massive_results(seat=seat, season=season_4, results=results_bye_streak)

        self.assertEqual(driver.get_streak(**record_config), 1)
        self.assertEqual(driver.get_streak(result_filter={'competition': competition_1}, **record_config), 1)
        self.assertEqual(driver.get_season(season_4).get_streak(**record_config), 1)
        self.assertEqual(driver.get_streak(max_streak=True, **record_config), 13)
        self.assertEqual(driver.get_streak(max_streak=True, result_filter={'competition': competition_1},
                                           **record_config), 8)
        self.assertEqual(driver.get_season(season_4).get_streak(max_streak=True, **record_config), 2)
        # and records in competition_2/season_3 are not altered
        self.assertEqual(driver.get_streak(result_filter={'competition': competition_2}, **record_config), 5)
        self.assertEqual(driver.get_season(season_3).get_streak(**record_config), 5)

        # check records
        self.assertEqual(driver.get_stats(**record_config), 19, 'Global record')
        self.assertEqual(driver.get_stats(competition=competition_1, **record_config), 14, 'Record in comp_1')
        self.assertEqual(driver.get_stats(competition=competition_2, **record_config), 5, 'Record in comp_2')
        self.assertEqual(driver.get_stats(season=season_1, **record_config), 7, 'Record in season_1')
        self.assertEqual(driver.get_stats(season=season_2, **record_config), 4, 'Record in season_2')
        self.assertEqual(driver.get_stats(season=season_3, **record_config), 5, 'Record in season_3')
        self.assertEqual(driver.get_stats(season=season_4, **record_config), 3, 'Record in season_4')

        self.assertTrue(driver.is_active)

        punctuation_config = get_punctuation_config('F1-10+6')

        self.assertEqual(driver.get_points(), 418)
        self.assertEqual(driver.get_points(punctuation_config=punctuation_config), 150)

        self.assertEqual(driver.get_points(season=season_4), 85)
        self.assertEqual(season_4.leader['points'], driver.get_points(season=season_4))

    def test_rank(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        self.get_test_competition_team(competition=competition, team=seat_a.team)
        result_a = self.get_test_result(seat=seat_a, race=race, qualifying=2, finish=1)

        seat_b = self.get_test_seat_teammate(seat_a=seat_a)
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
        self.assertEquals(season.leader['driver'], seat_a.driver) # seat a.driver is the winner, the leader
        self.assertEquals(season.team_leader['team'], seat_a.team)
        self.assertEqual(season.runner_up['driver'], seat_b.driver)

        # contenderseason.get_points
        driver_a = seat_a.driver
        contender_season = ContenderSeason(driver=driver_a, season=season)
        self.assertGreater(contender_season.get_points(), 0)
        self.assertGreater(contender_season.get_points(1), 0)

    def test_team_competition_validation(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition()
        season_year = 2018
        season = self.get_test_season(competition=competition, year=season_year)
        race = self.get_test_race(season=season, round=1)
        self.assertRaises(ValidationError, self.get_test_result, **{'seat': seat_a, 'race': race,
                                                                    'qualifying': 2, 'finish': 2})

    def test_period_limitation(self):
        period_year = 2017
        seat_a = self.get_test_seat()
        self.assertTrue(SeatPeriod.objects.create(seat=seat_a, from_year=period_year, until_year=period_year))

        competition = self.get_test_competition()
        season_year = 2018
        season = self.get_test_season(competition=competition, year=season_year)
        race = self.get_test_race(season=season, round=1)
        self.assertRaises(ValidationError, self.get_test_result, **{'seat': seat_a, 'race': race,
                                                                    'qualifying': 2, 'finish': 2})

    def test_rank_integrity(self):
        seat_a = self.get_test_seat()
        competition_a = self.get_test_competition()
        season_a = self.get_test_season(competition=competition_a, year=2018)
        race_season_a = self.get_test_race(season=season_a, round=1)
        self.get_test_competition_team(competition=competition_a, team=seat_a.team)

        result_a = self.get_test_result(seat=seat_a, race=race_season_a, qualifying=1, finish=1)
        self.assertEqual(season_a.leader['points'], 25)

        season_b = self.get_test_season(competition=competition_a, year=2019)
        race_season_b = self.get_test_race(season=season_b, round=1)
        result_b = self.get_test_result(seat=seat_a, race=race_season_b, qualifying=1, finish=1)

        rank_b = season_b.points_rank()
        self.assertEqual(season_b.leader['points'], 25)

        rank_competition_a = competition_a.points_rank()
        leader_comp_a = rank_competition_a[0]
        self.assertEqual(leader_comp_a['points'], 50)

        competition_c = self.get_test_competition_2()
        season_c = self.get_test_season(competition=competition_c, year=2020)
        race_season_c = self.get_test_race(season=season_c, round=1)
        self.get_test_competition_team(competition=competition_c, team=seat_a.team)
        result_c = self.get_test_result(seat=seat_a, race=race_season_c, qualifying=1, finish=1)

        rank_c = season_c.points_rank()
        leader_c = rank_c[0]
        self.assertEqual(leader_c['points'], 25)

        rank_competition_c = competition_c.points_rank()
        leader_comp_c = rank_competition_c[0]
        self.assertEqual(leader_comp_c['points'], 25)

    def test_seat_team_exception(self):
        seat = self.get_test_seat()
        race = self.get_test_race()
        result_args = {'seat': seat, 'race': race, 'qualifying': 1, 'finish': 3}
        self.assertRaises(ValidationError, self.get_test_result, **result_args)

    def test_duplicate_driver(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition()
        self.assertTrue(self.get_test_competition_team(competition=competition, team=seat_a.team))
        season = self.get_test_season(competition=competition)
        race = self.get_test_race(season=season)
        result_a_args = {'seat': seat_a, 'race': race, 'qualifying': 1, 'finish': 3}
        result_a = self.get_test_result(**result_a_args)

        seat_a_other_team = self.get_test_seat_same_driver_other_team(seat_a)
        result_b_args = {'seat': seat_a_other_team, 'race': race, 'qualifying': 2, 'finish': 2}
        self.assertRaises(ValidationError, self.get_test_result, **result_b_args)
        self.assertEqual(race.results.count(), 1)

        # test swapfield. Seat_a loses the pole, Seat_b is poleman
        seat_b = self.get_test_seat_teammate(seat_a)
        self.assertTrue(self.get_test_result(seat=seat_b, race=race, qualifying=1, finish=3))
        self.assertEqual(race.results.count(), 2)
        self.assertEqual(race.pole, seat_b)


