# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import retro_encode, CommonTeamSeasonTestCase
from ..models import TeamSeason

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
        expected_team_season = '{team} in {season}'.format(team=team_season.team, season=season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))
        team_season.sponsor_name = 'Sponsored Team'
        self.assertIsNone(team_season.save())
        expected_team_season = '{sponsor} in {season}'.format(sponsor=team_season.sponsor_name, season=season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))