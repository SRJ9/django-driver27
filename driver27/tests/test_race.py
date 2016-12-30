# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import retro_encode, CommonRaceTestCase


class RaceTestCase(TestCase, CommonRaceTestCase):
    def test_circuit_unicode(self):
        circuit = self.get_test_circuit()
        expected_circuit = circuit.name
        self.assertEquals(str(circuit), retro_encode(expected_circuit))

    def test_race_unicode(self):
        race = self.get_test_race()
        expected_race = '{season}-{round}'.format(season=race.season, round=race.round)
        self.assertEquals(str(race), expected_race)
        return race

    def test_race_grandprix(self):
        race = self.get_test_race()
        season = race.season
        grand_prix = self.get_test_grandprix()
        # add grandprix without season
        race.grand_prix = grand_prix
        race.default_circuit = grand_prix.default_circuit
        self.assertRaises(ValidationError, race.save)
        # add season to grandprix
        self.assertIsNone(grand_prix.competitions.add(season.competition))
        self.assertIsNone(race.save())
        # expected race changes (adding grandprix to str)
        expected_race = '{season}-{round}.{grand_prix}'.format(season=season, round=race.round,
                                                               grand_prix=grand_prix)
        self.assertEquals(str(race), expected_race)

    def test_race_round_exception(self):
        race = self.get_test_race()
        race.round = 999
        self.assertRaises(ValidationError, race.save)
