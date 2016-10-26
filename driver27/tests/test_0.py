# -*- coding: utf-8 -*-
import sys
import copy
from django.test import TestCase
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from driver27.models import Driver, Competition, Team, Season, Circuit
from driver27.models import Contender, TeamSeason, Seat, GrandPrix, Race, Result, ContenderSeason
from slugify import slugify

def retro_encode(text):
    if sys.version_info < (3, 0):
        try:
            return text.encode('utf-8')
        except UnicodeDecodeError:
            return text
    else:
        return text

class CommonDriverTestCase(object):
    def set_test_driver(self, **kwargs):
        self.assertTrue(Driver.objects.create(year_of_birth=1985, **kwargs))
        return Driver.objects.get(**kwargs)

    def get_test_driver_a(self):
        test_driver_args = {'last_name': 'García', 'first_name': 'Juan'}
        return self.set_test_driver(**test_driver_args)

    def get_test_driver_b(self):
        test_driver_args = {'last_name': 'López', 'first_name': 'Jaime'}
        return self.set_test_driver(**test_driver_args)

class CommonCompetitionTestCase(object):
    def set_test_competition(self, **kwargs):
        self.assertTrue(Competition.objects.create(**kwargs))
        return Competition.objects.get(**kwargs)

    def get_test_competition_a(self):
        test_competition_args = {'name': 'Competición A', 'full_name': 'Competición ABC'}
        return self.set_test_competition(**test_competition_args)

    def get_test_competition_b(self):
        test_competition_args = {'name': 'Competición B', 'full_name': 'Competición BDF'}
        return self.set_test_competition(**test_competition_args)

class CommonTeamTestCase(object):
    def set_test_team(self, **kwargs):
        self.assertTrue(Team.objects.create(**kwargs))
        return Team.objects.get(**kwargs)

    def get_test_team(self):
        team_args = {'name': 'Escudería Tec Auto', 'full_name': 'Escudería Tec Auto'}
        return self.set_test_team(**team_args)

    def get_test_team_b(self):
        team_args = {'name': 'D27R', 'full_name': 'Driver 27 Racing Team'}
        return self.set_test_team(**team_args)

class CommonContenderTestCase(CommonDriverTestCase, CommonCompetitionTestCase):
    def set_test_contender(self, driver, competition):
        contender_args = {'driver': driver, 'competition': competition}
        self.assertTrue(Contender.objects.create(**contender_args))
        return Contender.objects.get(**contender_args)

    def get_test_contender(self):
        driver = self.get_test_driver_a()
        competition = self.get_test_competition_a()
        return self.set_test_contender(driver=driver, competition=competition)

    def get_test_contender_b(self, contender):
        driver = self.get_test_driver_b()
        competition = contender.competition
        return self.set_test_contender(driver=driver, competition=competition)



class CommonSeasonTestCase(CommonCompetitionTestCase):
    def set_test_season(self, **kwargs):
        self.assertTrue(Season.objects.create(**kwargs))
        return Season.objects.get(**kwargs)

    def get_test_season(self, competition):
        season_args = {'year': '2016', 'competition': competition}
        return self.set_test_season(**season_args)

class CommonTeamSeasonTestCase(CommonTeamTestCase, CommonSeasonTestCase):
    pass

class CommonSeatTestCase(CommonContenderTestCase, CommonTeamTestCase):
    def set_test_seat(self, **kwargs):
        self.assertTrue(Seat.objects.create(**kwargs))
        seat = Seat.objects.get(**kwargs)
        return seat

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
        return self.set_test_seat(**seat_args)

    def get_test_seat_b(self, seat_a):
        # different contender, same team
        contender = self.get_test_contender_b(contender=seat_a.contender)
        team = seat_a.team
        seat_args = {'contender': contender, 'team': team}
        # Seat 2 OK
        return self.set_test_seat(**seat_args)

    def get_test_seat_c(self, seat_a):
        # same contender A, different team
        contender = seat_a.contender
        team = self.get_test_team_b()
        # Add Team 1 to Competition A
        self.assertIsNone(team.competitions.add(contender.competition))
        seat_args = {'contender': contender, 'team': team}
        # Seat 3 OK
        return self.set_test_seat(**seat_args)


class CommonRaceTestCase(CommonSeasonTestCase):
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

    def get_test_race(self, competition = None):
        if not competition:
            competition = self.get_test_competition_a()
        season = self.get_test_season(competition=competition)
        race_args = {
            'round': 1,
            'season': season,
            'date': None,
            'alter_punctuation': None
        }
        # race without grandprix
        self.assertTrue(Race.objects.create(**race_args))
        race = Race.objects.get(season=season, round=1)
        return race

class CommonResultTestCase(CommonSeatTestCase, CommonRaceTestCase):
    def get_test_result(self, seat=None, race=None, raise_team_exception=False):
        # when raise_team_exception, the team-season will not be created
        # raise a exception, because the team is invalid in that season
        if not seat:
            seat = self.get_test_seat()
        competition = seat.contender.competition
        if not race:
            race = self.get_test_race(competition=competition)

        season = race.season
        if not raise_team_exception and seat.team not in season.teams.all():
            self.assertTrue(TeamSeason.objects.create(team=seat.team, season=season))
        result_args = {
            'seat': seat,
            'race': race,
            'qualifying': None,
            'finish': None,
            'fastest_lap': False,
            'retired': False,
            'wildcard': False,
            'comment': None
        }
        if raise_team_exception:
            self.assertRaises(ValidationError, Result.objects.create, **result_args)
        else:
            self.assertTrue(Result.objects.create(**result_args))
            result = Result.objects.get(**{'seat': seat, 'race': race})
            return result

class DriverTestCase(TestCase, CommonDriverTestCase):
    def test_driver_unicode(self):
        driver = self.get_test_driver_a()
        expected_unicode = ', '.join((driver.last_name, driver.first_name))
        self.assertEquals(str(driver), retro_encode(expected_unicode))

    def test_driver_save_exception(self):
        driver = self.get_test_driver_a()
        driver.year_of_birth = 1885
        self.assertRaises(ValidationError, driver.save)

class CompetitionTestCase(TestCase, CommonCompetitionTestCase):
    def test_competition_unicode(self):
        competition = self.get_test_competition_a()
        self.assertEquals(competition.slug, slugify(competition.name))
        self.assertEqual(str(competition), retro_encode(competition.name))

class TeamTestCase(TestCase, CommonTeamTestCase):
    def test_team_unicode(self):
        team = self.get_test_team()
        self.assertTrue(str(team), team.name)

class ContenderTestCase(TestCase, CommonContenderTestCase):
    def test_contender_unicode(self):
        contender = self.get_test_contender()
        expected_str = ' in '.join((str(contender.driver), str(contender.competition)))
        self.assertEquals(str(contender), expected_str)

    def test_contender_team(self):
        contender = self.get_test_contender()
        self.assertEquals(contender.teams_verbose, None)


class SeasonTestCase(TestCase, CommonSeasonTestCase, CommonSeatTestCase):
    def test_season_unicode(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        expected_season = '%s/%s' % (str(season.competition), season.year)
        self.assertEquals(str(season), expected_season)

    def test_season_scoring(self):
        competition = self.get_test_competition_a()
        season = self.get_test_season(competition)
        self.assertIsNone(season.get_scoring())
        season.punctuation = 'F1-25'
        self.assertIsNone(season.save())
        self.assertIsInstance(season.get_scoring(), dict)

    def test_season_contenders(self):
        seat_a = self.get_test_seat()
        team_a = seat_a.team
        competition = seat_a.contender.competition
        season = self.get_test_season(competition)
        seat_b = self.get_test_seat_b(seat_a=seat_a)
        seat_c = self.get_test_seat_c(seat_a=seat_a)
        team_c = seat_c.team
        # create TeamSeason rel, A and B is the same
        self.assertTrue(TeamSeason.objects.create(team=team_a, season=season))
        self.assertTrue(TeamSeason.objects.create(team=team_c, season=season))
        # create SeatSeason rel
        self.assertIsNone(seat_a.seasons.add(season))
        self.assertIsNone(seat_b.seasons.add(season))
        self.assertIsNone(seat_c.seasons.add(season))
        # A and C is the same, 2 = (A, B)
        self.assertEquals(season.contenders().count(), 2)

    def test_seat_season_exception(self):
        seat_a = self.get_test_seat()
        competition = self.get_test_competition_b()
        season = self.get_test_season(competition)
        team = seat_a.team
        with transaction.atomic():
            self.assertRaises(ValidationError, seat_a.seasons.add, season)
        # generate new seat (same driver, new competition, same team)
        contender_b_args = {'competition': competition, 'driver': seat_a.contender.driver}
        self.assertTrue(self.set_test_contender(**contender_b_args))
        contender_b = Contender.objects.get(**contender_b_args)
        # add team to competition
        self.assertIsNone(team.competitions.add(competition))
        # save seat_b
        seat_b_args = {'contender': contender_b, 'team': team}
        self.assertTrue(self.set_test_seat(**seat_b_args))
        seat_b = Seat.objects.get(**seat_b_args)
        # Fail again because Seat team is not in season
        with transaction.atomic():
            self.assertRaises(ValidationError, seat_b.seasons.add, season)
        # Save team-season rel and Seat-Season save is ok
        self.assertTrue(TeamSeason.objects.create(**{'team': team, 'season': season}))
        self.assertIsNone(seat_b.seasons.add(season))

class TeamSeasonTestCase(TestCase, CommonTeamSeasonTestCase):
    def test_team_season_validation(self):
        team = self.get_test_team()
        competition_b = self.get_test_competition_b()
        self.assertIsNone(team.competitions.add(competition_b))

        # Team is in Competition B / Season is in Competition A
        competition_a = self.get_test_competition_a()
        season = self.get_test_season(competition=competition_a)
        self.assertRaises(ValidationError,
                          TeamSeason.objects.create, **{'team': team, 'season': season})

        # Team is in Competition B + Competition A
        self.assertIsNone(team.competitions.add(season.competition))
        self.assertTrue(TeamSeason.objects.create(**{'team': team, 'season': season}))

    def test_team_season_unicode(self):

        team = self.get_test_team()
        competition_a = self.get_test_competition_a()
        season = self.get_test_season(competition=competition_a)
        self.assertIsNone(team.competitions.add(season.competition))
        team_season_args = {'team': team, 'season': season}
        self.assertTrue(TeamSeason.objects.create(**team_season_args))
        team_season = TeamSeason.objects.get(**team_season_args)
        # STR team_season
        expected_team_season = '%s in %s' % (team_season.team, season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))
        team_season.sponsor_name = 'Sponsored Team'
        self.assertIsNone(team_season.save())
        expected_team_season = '%s in %s' % (team_season.sponsor_name, season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))



class SeatTestCase(TestCase, CommonSeatTestCase):
    def test_seat_unicode(self):
        seat = self.get_test_seat()
        contender = seat.contender
        team = seat.team
        expected_seat = ' in '.join((str(contender.driver), str(team)))
        self.assertEquals(str(seat), expected_seat)

    def test_seat_current_unique(self):
        seat_a = self.get_test_seat()
        seat_a.current = True
        self.assertIsNone(seat_a.save())
        contender = seat_a.contender
        team_a = seat_a.team
        # create seat_c (same contender, different team)
        seat_c = self.get_test_seat_c(seat_a=seat_a)
        seat_c.current = True
        self.assertIsNone(seat_c.save())
        team_c = seat_c.team
        # # Although both seats have current=True, only the first is saved.
        self.assertEquals(Seat.objects.filter(contender=contender).count(), 2)
        self.assertEquals(Seat.objects.filter(contender=contender, current=True).count(), 1)
        self.assertEquals(Seat.objects.get(contender=contender, team=team_a).current, True)
        self.assertEquals(Seat.objects.get(contender=contender, team=team_c).current, False)




class RaceTestCase(TestCase, CommonRaceTestCase):
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




class ResultTestCase(TestCase, CommonResultTestCase):
    def test_result_shorcuts(self):
        result = self.get_test_result()
        self.assertEquals(result.driver, result.seat.contender.driver)
        self.assertEquals(result.team, result.seat.team)

    def test_result_fastest_unique(self):
        result = self.get_test_result()
        result.fastest_lap = True
        self.assertIsNone(result.save())
        seat_a = result.seat
        race = result.race
        # create result_b
        seat_b = self.get_test_seat_b(seat_a=seat_a)
        result_b = self.get_test_result(seat=seat_b, race=race)
        result_b.fastest_lap = True
        self.assertIsNone(result_b.save())
        # Although both results have fastest_lap=True, only the first is saved.
        self.assertEquals(Result.objects.filter(race=race, fastest_lap=True).count(), 1)
        self.assertEquals(Result.objects.get(race=race, seat=seat_a).fastest_lap, True)
        self.assertEquals(Result.objects.get(race=race, seat=seat_b).fastest_lap, False)

    def test_result_points(self):
        result = self.get_test_result()
        seat = result.seat
        race = result.race
        season = race.season
        season.punctuation = 'F1-25'
        self.assertIsNone(season.save())

        result.qualifying = 2
        result.finish = 2
        self.assertIsNone(result.save())

        # result.finish = 2 = ?? points
        self.assertGreater(result.points, 0)
        team_season = TeamSeason.objects.get(team=seat.team, season=season)
        self.assertGreater(team_season.get_points(), 0)
        race_points = result.points

        # change scoring to add fastest_lap point
        scoring = season.get_scoring()
        scoring['fastest_lap'] = 1
        # result + fastest_lap
        result.fastest_lap = True
        self.assertIsNone(result.save())
        # result.points is greater than before
        self.assertGreater(result.points, race_points)
        self.assertEquals(race.fastest, result.seat)

    def test_result_team_exception(self):
        self.get_test_result(raise_team_exception=True)


class ContenderSeasonTestCase(TestCase, CommonSeatTestCase, CommonSeasonTestCase):
    def test_contender_season(self):
        contender = None
        season = None
        self.assertRaises(ValidationError, ContenderSeason,
                          **{'contender': contender, 'season': season})
        seat = self.get_test_seat()
        contender = seat.contender
        self.assertIsNone(contender.get_season(season))
        season = self.get_test_season(competition=contender.competition)
        self.assertTrue(ContenderSeason(contender=contender, season=season))
        self.assertIsInstance(contender.get_season(season), ContenderSeason)