# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import retro_encode, CommonRaceTestCase
from ..models import Race

class RaceTestCase(TestCase, CommonRaceTestCase):
    def test_circuit_unicode(self):
        circuit = self.get_test_circuit()
        expected_circuit = circuit.name
        self.assertEquals(str(circuit), retro_encode(expected_circuit))

    def test_race_unicode(self):
        race = self.get_test_race()
        expected_race = '%s-%s' % (race.season, race.round)
        self.assertEquals(str(race), expected_race)
        return race

    def test_race_grandprix(self):
        race = self.get_test_race()
        season = race.season
        grandprix = self.get_test_grandprix()
        # add grandprix without season
        race.grand_prix = grandprix
        race.default_circuit = grandprix.default_circuit
        self.assertRaises(ValidationError, race.save)
        # add season to grandprix
        self.assertIsNone(grandprix.competitions.add(season.competition))
        self.assertIsNone(race.save())
        # expected race changes (adding grandprix to str)
        expected_race = '%s-%s.%s' % (season, race.round, grandprix)
        self.assertEquals(str(race), expected_race)

    def test_race_round_exception(self):
        race = self.get_test_race()
        race.round = 999
        self.assertRaises(ValidationError, race.save)
