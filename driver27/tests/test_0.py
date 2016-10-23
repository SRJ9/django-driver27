# -*- coding: utf-8 -*-
import sys
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from driver27.models import Driver, Competition, Team, Contender, Seat, Season, Circuit, GrandPrix, Race
from driver27.models import ContenderSeason

from slugify import slugify

def encode_pyv(text):
    if sys.version_info < (3, 0):
        return text.encode('utf-8')
    else:
        return text

class ZeroTestCase(TestCase):

    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json', 'driver-competition-2016.json', 'driver-competition-team-2016.json',
    'races-2016.json']

    def test_okey(self):
        print('Se han cargado todos los fixtures')


    def get_test_driver(self):
        test_driver_args = {'last_name': 'García', 'first_name': 'Juan'}
        self.assertTrue(Driver.objects.create(year_of_birth=1985, **test_driver_args))
        return Driver.objects.get(**test_driver_args)

    def get_test_competition(self, no_create=False):
        test_competition_args = {'name': 'Competición A'}
        if no_create is False:
            self.assertTrue(Competition.objects.create(full_name='Competición ABC', **test_competition_args))
        return Competition.objects.get(**test_competition_args)


    def get_test_contender(self):
        driver = self.get_test_driver()
        competition = self.get_test_competition()
        # create Contender
        contender_args = {'driver': driver, 'competition': competition}
        self.assertTrue(Contender.objects.create(**contender_args))
        contender = Contender.objects.get(**contender_args)
        expected_str = ' in '.join((str(driver), str(competition)))
        self.assertEquals(str(contender), expected_str)
        return contender

    def get_test_team(self):
        # create Team 1 to Seat 1
        team_args = {'name': 'Escudería Tec Auto', 'full_name': 'Escudería Tec Auto'}
        self.assertTrue(Team.objects.create(**team_args))
        team = Team.objects.get(**team_args)
        return team

    def get_test_seat(self):
        contender = self.get_test_contender()
        competition = contender.competition
        team = self.get_test_team()
        seat_args = {'contender': contender, 'team': team}
        # Team 1 not is a team of Competition A
        self.assertRaises(ValidationError, Seat.objects.create, **seat_args)
        # Add Team 1 to Competition A
        self.assertIsNone(team.competitions.add(competition))
        # Seat 1 OK
        self.assertTrue(Seat.objects.create(**seat_args))
        seat = Seat.objects.get(**seat_args)
        expected_seat = ' in '.join((str(contender.driver), str(team)))
        self.assertEquals(str(seat), expected_seat)
        seat.current = True
        self.assertIsNone(seat.save())
        return seat

    def get_test_season(self, exclude_competition_create=False):
        competition = self.get_test_competition(no_create=exclude_competition_create)
        season_args = {'year': '2016', 'competition': competition}
        self.assertTrue(Season.objects.create(**season_args))
        season = Season.objects.get(**season_args)
        self.assertIsNone(season.get_scoring())
        expected_season = '%s/%s' % (str(season.competition), season.year)
        self.assertEquals(str(season), expected_season)
        return season

    def get_test_circuit(self):
        circuit_args = {"name": "Autódromo de Jacarepaguá", "city": "Jacarepaguá"}
        self.assertTrue(Circuit.objects.create(country='BR', opened_in=1978, **circuit_args))
        circuit = Circuit.objects.get(**circuit_args)
        return circuit

    def get_test_grandprix(self):
        circuit = self.get_test_circuit()
        grandprix_args = {'name': 'Grande Prêmio do Brasil'}
        self.assertTrue(GrandPrix.objects.create(
            default_circuit=circuit, country='BR', first_held=1972, **grandprix_args))
        return GrandPrix.objects.get(**grandprix_args)

    def test_driver_unicode(self):
        driver = self.get_test_driver()
        expected_unicode = ', '.join((driver.last_name, driver.first_name))
        self.assertEquals(str(driver), encode_pyv(expected_unicode))

    def test_driver_save_exception(self):
        driver = self.get_test_driver()
        driver.year_of_birth = 1885
        self.assertRaises(ValidationError, driver.save)

    def test_competition_save(self):
        competition = self.get_test_competition()
        self.assertEquals(competition.slug, slugify(competition.name))
        self.assertEqual(str(competition), encode_pyv(competition.name))

    def test_team_save(self):
        team = self.get_test_team()
        self.assertTrue(str(team), team.name)

    def test_contender_save(self):
        contender = self.get_test_contender()
        self.assertEquals(contender.teams_verbose, None)

    def test_seat_save(self):
        seat1 = self.get_test_seat()
        # Create Seat 2 to check only one current seat by Contender
        contender = seat1.contender
        competition = contender.competition
        # team 2 to Contender
        team2_args = {'name': 'Team 2', 'full_name': 'Team 246'}
        self.assertTrue(Team.objects.create(**team2_args))
        team2 = Team.objects.get(**team2_args)
        # Add Team 2 to Competition A
        self.assertIsNone(team2.competitions.add(competition))
        seat2_args = {'contender': contender, 'team': team2}
        # Seat 2 OK
        self.assertTrue(Seat.objects.create(current=True, **seat2_args))
        seat2 = Seat.objects.get(**seat2_args)
        # Seat 2 current is False, because Seat 1 is Contender current Seat.
        self.assertFalse(seat2.current)

    def test_season(self):
        seat = self.get_test_seat()
        season = self.get_test_season(exclude_competition_create=True)
        season.punctuation = 'F1-25'
        self.assertIsNone(season.save())
        self.assertIsInstance(season.get_scoring(), dict)
        self.assertEqual(season.contenders().count(), 0)
        self.assertIsNone(seat.seasons.add(season))
        self.assertIn(seat.contender, season.contenders())

        # competition b
        test_competition_args = {'name': 'Competición B'}
        self.assertTrue(Competition.objects.create(full_name='Competición BDF', **test_competition_args))
        competition_b = Competition.objects.get(**test_competition_args)
        # season b
        season.pk = None
        season.competition = competition_b
        self.assertIsNone(season.save())
        expected_season = '%s/%s' % (competition_b, season.year)
        self.assertEquals(str(season), expected_season)
        self.assertRaises(ValidationError, seat.seasons.add, season)

    def test_circuit(self):
        circuit = self.get_test_circuit()
        self.assertEquals(str(circuit), encode_pyv(circuit.name))

    def test_grandprix(self):
        grandprix = self.get_test_grandprix()
        competition = self.get_test_competition()
        self.assertIsNone(grandprix.competitions.add(competition))
        self.assertEquals(str(grandprix), encode_pyv(grandprix.name))

    def test_race(self):
        season = self.get_test_season()
        grandprix = self.get_test_grandprix()
        race_args = {
            'round': 1,
            'season': season,
            # 'grand_prix': grandprix,
            'date': None,
            # 'circuit': grandprix.default_circuit,
            'alter_punctuation': None
        }

        # race without grandprix
        self.assertTrue(Race.objects.create(**race_args))
        race = Race.objects.get(season=season, round=1)
        expected_race = '%s-%s' % (season, race.round)
        self.assertEquals(str(race), expected_race)
        # add grandprix without season
        race.grand_prix = grandprix
        race.default_circuit = grandprix.default_circuit
        self.assertRaises(ValidationError, race.save)
        # add season to competition
        self.assertIsNone(grandprix.competitions.add(season.competition))
        self.assertIsNone(race.save())
        race = Race.objects.get(season=season, round=1)
        # expected race changes (adding grandprix to str)
        expected_race = '%s-%s.%s' % (season, race.round, grandprix)
        self.assertEquals(str(race), expected_race)

    def test_contender_season(self):
        contender = None
        season = None
        self.assertRaises(ValidationError, ContenderSeason, **{'contender': Contender, 'season': Season})
        seat = self.get_test_seat()
        contender = seat.contender
        self.assertIsNone(contender.get_season(season))
        season = self.get_test_season(exclude_competition_create=True)
        self.assertTrue(ContenderSeason(contender=contender, season=season))
        self.assertIsInstance(contender.get_season(season), ContenderSeason)









