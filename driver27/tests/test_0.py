# coding=utf-8
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from driver27.models import Driver, Competition, Team, Contender, Seat

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
        test_competition_args = {'name': 'Competition A', 'full_name': 'Competition ABC'}
        self.assertTrue(Competition.objects.create(**test_competition_args))

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

    def test_contender_and_seat(self):
        self.set_test_contender()
        driver = Driver.objects.get(last_name='García', first_name='Juan')
        competition = Competition.objects.get(name='Competition A')
        contender_args = {'driver': driver, 'competition': competition}
        # Contender
        self.assertTrue(Contender.objects.create(**contender_args))
        contender = Contender.objects.get(**contender_args)
        self.assertEquals(contender.teams_verbose, None)
        expected_str = ' in '.join((str(driver), str(competition)))
        self.assertEquals(str(contender), expected_str)
        # Seat
        team_args = {'name': 'Team 1', 'full_name': 'Team 123'}
        self.assertTrue(Team.objects.create(**team_args))
        team = Team.objects.get(**team_args)
        seat_args = {'contender': contender, 'team': team}
        # Team 1 not is a team of Competition A
        self.assertRaises(ValidationError, Seat.objects.create, **seat_args)
        # Add Team 1 to Competition A
        self.assertIsNone(team.competitions.add(competition))
        # Seat OK
        self.assertTrue(Seat.objects.create(**seat_args))
        seat = Seat.objects.get(**seat_args)
        expected_seat = ' in '.join((str(contender.driver), str(team)))
        self.assertEquals(str(seat), expected_seat)

