# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonSeatTestCase
from ..models import Seat

class SeatTestCase(TestCase, CommonSeatTestCase):
    def test_seat_unicode(self):
        seat = self.get_test_seat()
        contender = seat.contender
        team = seat.team
        expected_seat = '{driver} in {team}/{competition}'.format(driver=str(contender.driver), team=str(team),
                                                                  competition=str(contender.competition))
        self.assertEquals(str(seat), expected_seat)

    def test_seat_current_unique(self):
        seat_a = self.get_test_seat()
        seat_a.current = True
        self.assertIsNone(seat_a.save())
        contender = seat_a.contender
        team_a = seat_a.team
        self.assertEquals(Seat.objects.get(contender=contender, team=team_a).current, True)
        # create seat_c (same contender, different team)
        seat_c = self.get_test_seat_c(seat_a=seat_a)
        seat_c.current = True
        self.assertIsNone(seat_c.save())
        team_c = seat_c.team
        # # Although both seats have current=True, only the LAST is saved.
        self.assertEquals(Seat.objects.filter(contender=contender).count(), 2)
        self.assertEquals(Seat.objects.filter(contender=contender, current=True).count(), 1)
        self.assertEquals(Seat.objects.get(contender=contender, team=team_a).current, False)
        self.assertEquals(Seat.objects.get(contender=contender, team=team_c).current, True)
