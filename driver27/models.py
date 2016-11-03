# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, pre_save
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible
from . import punctuation
from slugify import slugify
from django_countries.fields import CountryField
from exclusivebooleanfield.fields import ExclusiveBooleanField

@python_2_unicode_compatible
class Driver(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=25)
    year_of_birth = models.IntegerField()
    country = CountryField()
    competitions = models.ManyToManyField('Competition', through='Contender', related_name='drivers')

    def clean(self):
        if self.year_of_birth < 1900 or self.year_of_birth > 2099:
            raise ValidationError('Year_of_birth must be between 1900 and 2099')
        super(Driver, self).clean()

    def __str__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')
        ordering = ['last_name', 'first_name']

@python_2_unicode_compatible
class Competition(models.Model):
    name = models.CharField(max_length=30, verbose_name='competition', unique=True)
    full_name = models.CharField(max_length=100, unique=True)
    country = CountryField(null=True, blank=True, default=None)
    slug = models.SlugField(null=True, blank=True, default=None)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Competition, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

@python_2_unicode_compatible
class Contender(models.Model):
    driver = models.ForeignKey(Driver, related_name='career')
    competition = models.ForeignKey('Competition', related_name='contenders')
    teams = models.ManyToManyField('Team', through='Seat', related_name='contenders')

    def get_season(self, season):
        try:
            contender_season = ContenderSeason(self, season)
            return contender_season
        except ValidationError:
            return None

    @property
    def teams_verbose(self):
        teams = self.teams
        return ', '.join([team.name for team in teams.all()]) if teams.count() else None

    def __str__(self):
        return '%s in %s' % (self.driver, self.competition)

    class Meta:
        unique_together = ('driver', 'competition')
        ordering = ['competition__name', 'driver__last_name', 'driver__first_name']

@python_2_unicode_compatible
class Team(models.Model):
    name = models.CharField(max_length=75, verbose_name='team', unique=True)
    full_name = models.CharField(max_length=200, unique=True)
    competitions = models.ManyToManyField('Competition', related_name='teams')
    country = CountryField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

@python_2_unicode_compatible
class Seat(models.Model):
    team = models.ForeignKey('Team', related_name='seats')
    contender = models.ForeignKey('Contender', related_name='seats')
    current = ExclusiveBooleanField(on='contender', default=False)
    seasons = models.ManyToManyField('Season', related_name='seats', blank=True, default=None)

    def clean(self):
        if self.contender.competition not in self.team.competitions.all():
            raise ValidationError(
                "%s is not a team of %s" % (self.team, self.contender.competition)
            )
        super(Seat, self).clean()

    def __str__(self):
        return '%s in %s' % (self.contender.driver, self.team)

    class Meta:
        unique_together = ('team', 'contender')
        ordering = ['contender__driver__last_name', 'team']

def seat_season(sender, instance, action, pk_set, **kwargs):
    # """ Signal in DriverCompetitionTeam.seasons to avoid seasons which not is in competition"""
    if action == 'pre_add':
        contender_competition = instance.contender.competition
        contender_seasons = [season.pk for season in contender_competition.seasons.all()]
        team_seasons = [season.pk for season in instance.team.seasons.all()]
        errors = []
        for pk in list(pk_set):
            pk_season = Season.objects.get(pk=pk)
            if int(pk) not in contender_seasons:
                errors.append(
                    '%s is not a/an %s season' % (pk_season, contender_competition)
                )
            if int(pk) not in team_seasons:
                errors.append(
                    '%s is not a team of %s' % (instance.team, pk_season)
                )
        if errors:
            raise ValidationError(errors)

m2m_changed.connect(seat_season, sender=Seat.seasons.through)

@python_2_unicode_compatible
class Circuit(models.Model):
    name = models.CharField(max_length=30, verbose_name='circuit', unique=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField()
    opened_in = models.IntegerField()

    # @todo Add Clockwise and length
    def __str__(self):
        # @todo Add country name in __str__
        return self.name

    class Meta:
        ordering = ['name']

@python_2_unicode_compatible
class GrandPrix(models.Model):
    name = models.CharField(max_length=30, verbose_name='grand prix', unique=True)
    country = CountryField(null=True, blank=True, default=None)
    first_held = models.IntegerField(null=True, blank=True)
    default_circuit = models.ForeignKey(Circuit, related_name='default_to_grands_prix', null=True, blank=True, default=None)
    competitions = models.ManyToManyField('Competition', related_name='grands_prix', default=None)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'grands prix'
        ordering = ['name']


@python_2_unicode_compatible
class Season(models.Model):
    year = models.IntegerField()
    competition = models.ForeignKey(Competition, related_name='seasons')
    rounds = models.IntegerField(blank=True, null=True, default=None)
    teams = models.ManyToManyField(Team, related_name='seasons', through='TeamSeason')
    punctuation = models.CharField(max_length=20, null=True, default=None)

    def get_scoring(self):
        for scoring in punctuation.DRIVER27_PUNCTUATION:
            if scoring['code'] == self.punctuation:
                return scoring
        return None

    def contenders(self):
        seats = [seat.pk for seat in self.seats.all()]
        return Contender.objects.filter(seats__pk__in=seats).distinct()

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
            team_season = TeamSeason.objects.get(season=self, team=team)
            rank.append((team_season.get_points(), team))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def get_leader(self, team=False):
        if team:
            rank = self.team_points_rank()
        else:
            rank = self.points_rank()
        return rank[0] if len(rank) else None


    @property
    def leader(self):
        return self.get_leader()

    @property
    def team_leader(self):
        return self.get_leader(team=True)

    def __str__(self):
        return '/'.join((self.competition.name, str(self.year)))

    class Meta:
        unique_together = ('year', 'competition')
        ordering = ['competition__name', 'year']

@python_2_unicode_compatible
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

    def _grandprix_exception(self):
        competition = self.season.competition
        if competition and self.grand_prix and competition not in self.grand_prix.competitions.all():
            return True
        else:
            return False

    def clean(self, *args, **kwargs):
        errors = {}
        season = getattr(self, 'season', None)
        if season:
            if self.round > self.season.rounds:
                errors['round'] = 'Max rounds in this season: %d' % self.season.rounds
            if self._grandprix_exception():
                errors['grand_prix'] = "%s is not a/an %s Grand Prix" % (self.grand_prix, self.season.competition)
        if errors:
            raise ValidationError(errors)
        super(Race, self).clean(*args, **kwargs)

    def get_result_seat(self, *args, **kwargs):
        results = self.results.filter(**kwargs)
        return results.first().seat if results.count() else None

    @property
    def pole(self):
        return self.get_result_seat(qualifying=1)

    @property
    def winner(self):
        return self.get_result_seat(finish=1)

    @property
    def fastest(self):
        return self.get_result_seat(fastest_lap=True)

    def __str__(self):
        race_str = '%s-%s' % (self.season, self.round)
        if self.grand_prix:
            race_str += '.%s' % self.grand_prix
        return race_str

    class Meta:
        unique_together = ('season', 'round')
        ordering = ['season', 'round']


@python_2_unicode_compatible
class TeamSeason(models.Model):
    season = models.ForeignKey('Season', related_name='teams_season')
    team = models.ForeignKey('Team', related_name='seasons_team')
    sponsor_name = models.CharField(max_length=75, null=True, blank=True, default=None)

    def clean(self, *args, **kwargs):
        team = self.team
        team_competitions = [competition.pk for competition in team.competitions.all()]
        if self.season.competition.pk not in team_competitions:
            raise ValidationError(
                'Team %s doesn\'t participate in %s' % (self.team, self.season.competition)
            )
        super(TeamSeason, self).clean(*args, **kwargs)

    def get_points(self):
        results = Result.objects.filter(race__season=self.season, seat__team=self.team) \
            .exclude(wildcard=True) \
            .order_by('race__round')
        points_list = [result.points for result in results.all() if result.points is not None]
        return sum(points_list)

    def __str__(self):
        str_team = self.team.name
        if self.sponsor_name:
            str_team = self.sponsor_name
        return '%s in %s' % (str_team, self.season)

    class Meta:
        unique_together = ('season', 'team')
        verbose_name = 'Team Season'
        verbose_name_plural = 'Teams Season'

class Result(models.Model):
    race = models.ForeignKey(Race, related_name='results')
    seat = models.ForeignKey(Seat, related_name='results')
    qualifying = models.IntegerField(blank=True, null=True, default=None)
    finish = models.IntegerField(blank=True, null=True, default=None)
    fastest_lap = ExclusiveBooleanField(on='race', default=False)
    retired = models.BooleanField(default=False)
    wildcard = models.BooleanField(default=False)
    comment = models.CharField(max_length=250, blank=True, null=True, default=None)

    def clean(self, *args, **kwargs):
        seat_errors = []
        if self.seat.team not in self.race.season.teams.all():
            seat_errors.append('Team is not in current season')
        if self.seat not in self.race.season.seats.all():
            seat_errors.append('Seat is not in current season')
        if seat_errors:
            raise ValidationError('Invalid Seat in this race. '+'\n'.join(seat_errors))
        super(Result, self).clean(*args, **kwargs)

    @property
    def driver(self):
        return self.seat.contender.driver

    @property
    def team(self):
        return self.seat.team

    def _get_fastest_lap_points(self, scoring):
        if 'fastest_lap' in scoring and self.fastest_lap:
            return scoring['fastest_lap']
        else:
            return 0

    def _get_race_points(self, scoring):
        race = self.race
        points_factor = {'double': 2, 'half': 0.5}
        factor = points_factor[race.alter_punctuation] if race.alter_punctuation in points_factor else 1
        points_scoring = sorted(scoring['finish'], reverse=True)
        if self.finish:
            scoring_len = len(points_scoring)
            if self.finish <= scoring_len:
                return points_scoring[self.finish - 1] * factor
        return 0

    @property
    def points(self):
        # @todo allow scoring simulate in future
        scoring = self.race.season.get_scoring()
        points = 0
        if scoring:
            points += self._get_fastest_lap_points(scoring)
            points += self._get_race_points(scoring)
        return points if points > 0 else None


    class Meta:
        unique_together = [('race', 'seat'), ('race', 'qualifying'), ('race', 'finish')]
        ordering = ['race__season', 'race__round', 'finish', 'qualifying']


class ContenderSeason(object):
    contender = None
    season = None
    teams = None
    contender_teams = None
    teams_verbose = None

    def __init__(self, contender, season):
        if not isinstance(contender, Contender) or not isinstance(season, Season):
            raise ValidationError('contender is not a Contender or/and season is not a Season')
        self.contender = contender
        self.season = season
        self.seats = Seat.objects.filter(contender__pk=self.contender.pk, seasons__pk=self.season.pk)
        self.teams = Team.objects.filter(seats__in=self.seats)
        self.teams_verbose = ', '.join([team.name for team in self.teams])


    def get_points(self, limit_races=None):
        results = Result.objects.filter(race__season=self.season, seat__contender=self.contender)
        if isinstance(limit_races, int):
            results = results.filter(race__round__lte=limit_races)
        results = results.order_by('race__round')
        points_list = [result.points for result in results.all() if result.points is not None]
        return sum(points_list)

@receiver(pre_save)
def pre_save_handler(sender, instance, *args, **kwargs):
    model_list = (Driver, Team, Competition, Contender, Seat, Circuit, GrandPrix, Race, Season, Result, TeamSeason)
    if isinstance(instance, model_list):
        instance.full_clean()
