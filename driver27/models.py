from __future__ import unicode_literals

import datetime
from django.db import models
from django.core.exceptions import ValidationError
import punctuation
from slugify import slugify

try:
    from django_countries.fields import CountryField
except ImportError:
    raise (
        'You are using the `driver27` app which requires the `django-countries` module.'
        'Be sure to add `django_countries` to your INSTALLED_APPS for `driver27` to work properly.'
    )

class Driver(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=25)
    year_of_birth = models.IntegerField()
    country = CountryField()
    competitions = models.ManyToManyField('Competition', through='DriverCompetition')

    def save(self, *args, **kwargs):
        if self.year_of_birth < 1900 or self.year_of_birth > 2099:
            raise ValidationError('Year_of_birth must be between 1900 and 2099')
        super(Driver, self).save(*args, **kwargs)

    def __unicode__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')
        ordering = ['last_name', 'first_name']

class DriverCompetitionTeam(models.Model):
    team = models.ForeignKey('Team', related_name='partners')
    enrolled = models.ForeignKey('DriverCompetition', related_name='squad')
    current = models.BooleanField(default=False)
    seasons = models.ManyToManyField('Season', blank=True, default=None)

    def __unicode__(self):
        return '%s %s %s' % (self.enrolled.driver, 'in', self.team)

    class Meta:
        unique_together = [('team', 'enrolled'), ('enrolled', 'current')]
        ordering = ['enrolled__driver__last_name', 'team']

class DriverCompetition(models.Model):
    driver = models.ForeignKey(Driver, related_name='career')
    competition = models.ForeignKey('Competition', related_name='career')
    teams = models.ManyToManyField('Team', through='DriverCompetitionTeam')

    def get_season(self, season):
        contender_season = ContenderSeason(self, season)
        contender_season.set_teams()
        return contender_season

    @property
    def teams_verbose(self):
        teams = self.teams
        return ', '.join([team.name for team in teams.all()]) if teams.count() else None

    def __unicode__(self):
        return '%s %s %s' % (self.driver, 'in', self.competition)

    class Meta:
        unique_together = ('driver', 'competition')
        ordering = ['competition__name', 'driver__last_name', 'driver__first_name']


class Team(models.Model):
    name = models.CharField(max_length=75, verbose_name='team', unique=True)
    full_name = models.CharField(max_length=200, unique=True)
    competitions = models.ManyToManyField('Competition', related_name='teams')
    country = CountryField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Competition(models.Model):
    name = models.CharField(max_length=30, verbose_name='competition', unique=True)
    full_name = models.CharField(max_length=100, unique=True)
    country = CountryField(null=True, blank=True, default=None)
    slug = models.SlugField(null=True, blank=True, default=None)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Competition, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Circuit(models.Model):
    name = models.CharField(max_length=30, verbose_name='circuit', unique=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField()
    opened_in = models.IntegerField()

    # @todo Add Clockwise and length
    def __unicode__(self):
        # @todo Add country name in __unicode__
        return self.name

    class Meta:
        ordering = ['name']

class GrandPrix(models.Model):
    name = models.CharField(max_length=30, verbose_name='grand prix', unique=True)
    country = CountryField(null=True, blank=True, default=None)
    first_held = models.IntegerField(null=True, blank=True)
    default_circuit = models.ForeignKey(Circuit, related_name='default_to_grands_prix', null=True, blank=True, default=None)
    competitions = models.ManyToManyField('Competition', related_name='grands_prix', default=None)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'grands prix'
        ordering = ['name']


class Season(models.Model):
    year = models.IntegerField()
    competition = models.ForeignKey(Competition, related_name='seasons')
    rounds = models.IntegerField(blank=True, null=True, default=None)
    teams = models.ManyToManyField(Team, related_name='seasons', through='TeamSeasonRel')
    punctuation = models.CharField(max_length=20, null=True, default=None)

    def get_scoring(self):
        for scoring in punctuation.DRIVER27_PUNCTUATION:
            if scoring['code'] == self.punctuation:
                return scoring
        return None

    def contenders(self):
        return DriverCompetition.objects.filter(squad__seasons__exact=self).distinct()

    def points_rank(self):
        contenders = self.contenders()
        rank = []
        for contender in contenders:
            contender_season = contender.get_season(self)
            rank.append((contender_season.get_points(), contender.driver, contender_season.teams_verbose))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def team_points_rank(self):
        teams = self.teams.all()
        rank = []
        for team in teams:
            team_season = TeamSeasonRel.objects.get(season=self, team=team)
            rank.append((team_season.get_points(), team))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank


    @property
    def leader(self):
        rank = self.points_rank()
        return rank[0]

    @property
    def team_leader(self):
        rank = self.team_points_rank()
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank[0]

    def __unicode__(self):
        return '/'.join((self.competition.name, str(self.year)))

    class Meta:
        unique_together = ('year', 'competition')
        ordering = ['competition__name', 'year']

class Race(models.Model):
    ALTER_PUNCTUATION = (
        ('double', 'Double'),
        ('half', 'Half')
    )
    season = models.ForeignKey(Season, related_name='races')
    round = models.IntegerField()
    grand_prix = models.ForeignKey(GrandPrix, related_name='races', blank=True, null=True, default=None)
    circuit = models.ForeignKey(Circuit, related_name='races', blank=True, null=True, default=None)
    date = models.DateField(blank=True, null=True, default=None)
    alter_punctuation = models.CharField(choices=ALTER_PUNCTUATION, null=True, blank=True, default=None, max_length=6)

    def save(self, *args, **kwargs):
        if self.season.competition not in self.grand_prix.competitions.all():
            raise ValidationError(
                "%s is not a/an %s Grand Prix" % (self.grand_prix, self.season.competition)
            )
        super(Race, self).save(*args, **kwargs)

    @property
    def pole(self):
        return self.results.get(qualifying=1)

    @property
    def winner(self):
        return self.results.get(finish=1)

    def __unicode__(self):
        race_str = str(self.season) + '-'+str(self.round)
        if self.grand_prix:
            race_str += '.' + str(self.grand_prix)
        return race_str

    class Meta:
        unique_together = ('season', 'round')
        ordering = ['season', 'round']

class TeamSeasonRel(models.Model):
    season = models.ForeignKey('Season')
    team = models.ForeignKey('Team')
    sponsor_name = models.CharField(max_length=75, null=True, blank=True, default=None)

    def save(self, *args, **kwargs):
        if self.season.competition not in self.team.competitions.all():
            raise ValidationError(
                'Team %s doesn\'t participate in %s' % (self.team, self.season.competition)
            )
        super(TeamSeasonRel, self).save(*args, **kwargs)

    def get_points(self):
        results = Result.objects.filter(race__season=self.season, contender__team=self.team) \
            .order_by('race__round')
        points_list = [result.points for result in results.all() if result.points is not None]
        return sum(points_list)

    class Meta:
        unique_together = ('season', 'team')
        verbose_name = 'Team Season'
        verbose_name_plural = 'Teams Season'

class Result(models.Model):
    race = models.ForeignKey(Race, related_name='results')
    contender = models.ForeignKey(DriverCompetitionTeam, related_name='results')
    qualifying = models.IntegerField(blank=True, null=True, default=None)
    finish = models.IntegerField(blank=True, null=True, default=None)
    fastest_lap = models.BooleanField(default=False)
    retired = models.BooleanField(default=False)
    comment = models.CharField(max_length=250, blank=True, null=True, default=None)

    @property
    def driver(self):
        return self.contender.enrolled.driver

    @property
    def team(self):
        return self.contender.team

    @property
    def points(self):
        race = self.race
        scoring = self.race.season.get_scoring()
        points = 0
        if scoring:
            if 'fastest_lap' in scoring and self.fastest_lap:
                points += scoring['fastest_lap']

            points_factor = {'double': 2, 'half': 0.5}
            factor = points_factor[race.alter_punctuation] if race.alter_punctuation in points_factor else 1
            points_scoring = sorted(scoring['finish'], reverse=True)
            if self.finish:
                scoring_len = len(points_scoring)
                if self.finish <= scoring_len:
                    points += points_scoring[self.finish-1]*factor
        return points if points > 0 else None


    class Meta:
        unique_together = [('race', 'contender'), ('race', 'qualifying'), ('race', 'finish')]
        ordering = ['race__season', 'race__round', 'finish', 'qualifying']


class ContenderSeason(object):
    contender = None
    season = None
    teams = None
    contender_teams = None
    teams_verbose = None

    def __init__(self, contender, season):
        self.contender = contender
        self.season = season


    def set_teams(self):
        self.contender_teams = DriverCompetitionTeam.objects.filter(enrolled__pk=self.contender.pk, seasons__pk=self.season.pk)
        self.teams = Team.objects.filter(partners__in=self.contender_teams)
        self.teams_verbose = ', '.join([team.name for team in self.teams])


    def get_points(self):
        results = Result.objects.filter(race__season=self.season, contender__enrolled=self.contender)\
            .order_by('race__round')
        points_list = [result.points for result in results.all() if result.points is not None]
        return sum(points_list)