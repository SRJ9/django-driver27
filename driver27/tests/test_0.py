# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from driver27.models import Driver, Competition, Team, Contender, Seat, Season

from slugify import slugify

class ZeroTestCase(TestCase):

    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json', 'driver-competition-2016.json', 'driver-competition-team-2016.json',
    'races-2016.json']

    def test_okey(self):
        print('Se han cargado todos los fixtures')

    def set_test_contender(self):
        test_driver_args = {'last_name': 'García', 'first_name': 'Juan', 'year_of_birth': 1985}
        self.assertTrue(Driver.objects.create(**test_driver_args))
        test_competition_args = {'name': 'Competición A', 'full_name': 'Competición ABC'}
        self.assertTrue(Competition.objects.create(**test_competition_args))

    def get_test_contender(self):
        self.set_test_contender()
        driver = Driver.objects.get(last_name='García', first_name='Juan')
        competition = Competition.objects.get(name='Competición A')
        # create Contender
        contender_args = {'driver': driver, 'competition': competition}
        self.assertTrue(Contender.objects.create(**contender_args))
        contender = Contender.objects.get(**contender_args)
        self.assertEquals(contender.teams_verbose, None)
        expected_str = ' in '.join((str(driver), str(competition)))
        self.assertEquals(str(contender), expected_str)
        return contender

    def get_test_seat(self):
        contender = self.get_test_contender()
        competition = contender.competition
        # create Team 1 to Seat 1
        team1_args = {'name': 'Team 1', 'full_name': 'Team 123'}
        self.assertTrue(Team.objects.create(**team1_args))
        team1 = Team.objects.get(**team1_args)
        seat1_args = {'contender': contender, 'team': team1}
        # Team 1 not is a team of Competition A
        self.assertRaises(ValidationError, Seat.objects.create, **seat1_args)
        # Add Team 1 to Competition A
        self.assertIsNone(team1.competitions.add(competition))
        # Seat 1 OK
        self.assertTrue(Seat.objects.create(**seat1_args))
        seat1 = Seat.objects.get(**seat1_args)
        expected_seat = ' in '.join((str(contender.driver), str(team1)))
        self.assertEquals(str(seat1), expected_seat)
        seat1.current = True
        self.assertIsNone(seat1.save())
        return seat1

    def get_test_season(self):
        seat = self.get_test_seat()
        competition = seat.contender.competition
        season_args = {'year': '2016', 'competition': competition}
        self.assertTrue(Season.objects.create(**season_args))
        season = Season.objects.get(**season_args)
        self.assertIsNone(season.get_scoring())
        season.punctuation = 'F1-25'
        self.assertIsNone(season.save())
        self.assertIsInstance(season.get_scoring(), dict)
        self.assertEqual(season.contenders().count(), 0)
        self.assertIsNone(seat.seasons.add(season))
        self.assertIn(seat.contender, season.contenders())
        expected_season = '{}/{}'.format(season.competition, season.year)
        self.assertEquals(str(season), expected_season)
        return season

    def test_driver_unicode(self):
        # test with hulkenberg, because he has unicode chars
        hulkenberg = Driver.objects.get(last_name='Hülkenberg', first_name='Nico')
        expected_unicode = ', '.join(('Hülkenberg', 'Nico'))
        self.assertEquals("%s" % hulkenberg, expected_unicode)

    def test_driver_save_exception(self):
        emmet_brown = {"last_name": "Brown", "first_name": "Emmet", "year_of_birth": 1885}
        self.assertRaises(ValidationError, Driver.objects.create, **emmet_brown)
        emmet_brown['year_of_birth'] = 1985
        self.assertTrue(Driver.objects.create(**emmet_brown))

    def test_competition_save(self):
        competition_args = {'name': 'Formula España', 'full_name': 'Formula Española 3'}
        self.assertTrue(Competition.objects.create(**competition_args))
        competition = Competition.objects.get(name='Formula España')
        self.assertEquals(competition.slug, slugify(competition.name))
        self.assertEquals(str(competition), competition_args['name'])
        # create duplicate competition
        self.assertRaises(IntegrityError, Competition.objects.create, **competition_args)

    def test_team_save(self):
        team_args = {'name': 'Escudería Tec Auto', 'full_name': 'Escudería Tec Auto'}
        self.assertTrue(Team.objects.create(**team_args))
        team = Team.objects.get(**team_args)
        self.assertTrue(str(team), team.name)

    def test_contender_save(self):
        contender = self.get_test_contender()

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
        season = self.get_test_season()




