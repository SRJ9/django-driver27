# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import retro_encode, CommonTeamSeasonTestCase
from ..models import TeamSeason, CompetitionTeam

class TeamSeasonTestCase(TestCase, CommonTeamSeasonTestCase):
    def test_team_season_validation(self):
        team = self.get_test_team()
        competition_b = self.get_test_competition_2()
        self.assertTrue(CompetitionTeam.objects.create(competition=competition_b, team=team))

    def test_team_season_unicode(self):

        team = self.get_test_team()
        competition_a = self.get_test_competition()
        season = self.get_test_season(competition=competition_a)
        self.assertTrue(CompetitionTeam.objects.create(competition=competition_a, team=team))
        team_season_args = {'team': team, 'season': season}
        self.assertTrue(TeamSeason.objects.create(**team_season_args))
        team_season = TeamSeason.objects.get(**team_season_args)
        # STR team_season
        expected_team_season = u'{team} in {season}'.format(team=team_season.team, season=season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))
        team_season.sponsor_name = 'Sponsored Team'
        self.assertIsNone(team_season.save())
        expected_team_season = u'{sponsor} in {season}'.format(sponsor=team_season.sponsor_name, season=season)
        self.assertEquals(str(team_season), retro_encode(expected_team_season))