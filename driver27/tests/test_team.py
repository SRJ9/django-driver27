# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonTeamTestCase
from ..models import Team


class TeamTestCase(TestCase, CommonTeamTestCase):
    def test_team_unicode(self):
        team = self.get_test_team()
        self.assertTrue(str(team), team.name)