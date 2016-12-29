# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .common import CommonSeasonTestCase, CommonSeatTestCase
from ..models import SeatSeason, TeamSeason, Contender, Seat


class SeasonTestCase(TestCase, CommonSeasonTestCase, CommonSeatTestCase):
    def test_season_unicode(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        year = season.year
        expected_season = '{competition}/{year}'.format(competition=competition, year=year)
        self.assertEquals(str(season), expected_season)

    def test_season_scoring(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertIsInstance(season.get_scoring(), dict)
        season.punctuation = 'BLABLABLA'
        self.assertIsNone(season.save())
        self.assertIsNone(season.get_scoring())

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
        team_a = seat_a.team
        competition = seat_a.contender.competition
        season = self.get_test_season(competition)
        seat_b = self.get_test_seat_b(seat_a=seat_a)
        seat_c = self.get_test_seat_c(seat_a=seat_a)
        team_c = seat_c.team
        # create TeamSeason rel, A and B is the same
        self.assertTrue(TeamSeason.objects.create(team=team_a, season=season))
        self.assertTrue(TeamSeason.objects.create(team=team_c, season=season))
        # create SeatSeason rel
        self.assertIsNone(seat_a.seasons.add(season))
        self.assertIsNone(seat_b.seasons.add(season))
        self.assertIsNone(seat_c.seasons.add(season))
        # A and C is the same, 2 = (A, B)
        self.assertEquals(season.contenders().count(), 2)

    def test_seat_season_exception(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition_b()
        season = self.get_test_season(competition)
        team = seat_a.team
        with transaction.atomic():
            self.assertRaises(ValidationError, seat_a.seasons.add, season)
        # generate new seat (same driver, new competition, same team)
        contender_b_args = {'competition': competition, 'driver': seat_a.contender.driver}
        self.assertTrue(self.set_test_contender(**contender_b_args))
        contender_b = Contender.objects.get(**contender_b_args)
        # add team to competition
        self.assertIsNone(team.competitions.add(competition))
        # save seat_b
        seat_b_args = {'contender': contender_b, 'team': team}
        self.assertTrue(self.set_test_seat(**seat_b_args))
        seat_b = Seat.objects.get(**seat_b_args)
        # Fail again because Seat team is not in season
        seat_season_args = {'seat': seat_b, 'season': season}
        with transaction.atomic():
            self.assertRaises(ValidationError, seat_b.seasons.add, season)
        self.assertRaises(ValidationError, SeatSeason.objects.create, **seat_season_args)
        # Save team-season rel and Seat-Season save is ok
        team_season_args = {'team': team, 'season': season}
        self.assertTrue(TeamSeason.objects.create(**team_season_args))
        self.assertTrue(SeatSeason.objects.create(**seat_season_args))
        team_season_filter = TeamSeason.objects.filter(**team_season_args)
        self.assertRaises(IntegrityError, team_season_filter.delete)
