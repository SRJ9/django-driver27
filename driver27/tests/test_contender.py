# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import CommonContenderTestCase

class ContenderTestCase(TestCase, CommonContenderTestCase):
    def test_contender_unicode(self):
        contender = self.get_test_contender()
        expected_str = ' in '.join((str(contender.driver), str(contender.competition)))
        self.assertEquals(str(contender), expected_str)

    def test_contender_team(self):
        contender = self.get_test_contender()
        self.assertEquals(contender.teams_verbose, None)