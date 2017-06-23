# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import CommonSeatTestCase, CommonSeasonTestCase
from ..models import ContenderSeason


class ContenderSeasonTestCase(TestCase, CommonSeatTestCase, CommonSeasonTestCase):
    def test_contender_season(self):
        driver = None
        season = None
        self.assertRaises(AttributeError, ContenderSeason,
                          **{'driver': driver, 'season': season})
        seat = self.get_test_seat()
        competition = self.get_test_competition()
        season = self.get_test_season(competition=competition)
        driver = seat.driver
        self.assertTrue(ContenderSeason(driver=driver, season=season))