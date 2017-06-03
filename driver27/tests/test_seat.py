# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonSeatTestCase
from ..models import Seat


class SeatTestCase(TestCase, CommonSeatTestCase):
    def test_seat_unicode(self):
        seat = self.get_test_seat()
        driver = seat.driver
        team = seat.team
        expected_seat = '{driver} in {team}'.format(driver=str(driver), team=str(team))
        self.assertEquals(str(seat), expected_seat)

