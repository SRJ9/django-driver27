# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import CommonSeatTestCase, CommonSeasonTestCase
from ..models import ContenderSeason


class ContenderSeasonTestCase(TestCase, CommonSeatTestCase, CommonSeasonTestCase):
    def test_contender_season(self):
        contender = None
        season = None
        self.assertRaises(ValidationError, ContenderSeason,
                          **{'contender': contender, 'season': season})
        seat = self.get_test_seat()
        contender = seat.contender
        self.assertIsNone(contender.get_season(season))
        season = self.get_test_season(competition=contender.competition)
        self.assertTrue(ContenderSeason(contender=contender, season=season))
        self.assertIsInstance(contender.get_season(season), ContenderSeason)