# -*- coding: utf-8 -*-
from django.test import TestCase
from .common import retro_encode, CommonCompetitionTestCase
from ..models import Competition
from slugify import slugify

class CompetitionTestCase(TestCase, CommonCompetitionTestCase):
    def test_competition_unicode(self):
        competition = self.get_test_competition_a()
        self.assertEquals(competition.slug, slugify(competition.name))
        self.assertEqual(str(competition), retro_encode(competition.name))