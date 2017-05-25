# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, IntegrityError
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, pre_save, pre_delete
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from .points_calculator import PointsCalculator
from .punctuation import get_punctuation_config
from .streak import Streak
from slugify import slugify
from django_countries.fields import CountryField
from exclusivebooleanfield.fields import ExclusiveBooleanField
from swapfield.fields import SwapIntegerField
from . import lr_intr, lr_diff, season_bulk_copy
from django.db.models.sql import constants
from .stats import AbstractStatsModel, TeamStatsModel
from .rank import AbstractRankModel

from collections import namedtuple

ResultTuple = namedtuple('ResultTuple', 'qualifying finish fastest_lap wildcard alter_punctuation')


def get_results(seat=None, contender=None, team=None,
                race=None, season=None, competition=None,
                limit_races=None,
                reverse_order=False,
                **extra_filters):
    key_in_filters = {
        'limit_races': 'race__round__lte',
        'contender': 'seat__contender',
        'team': 'seat__team',
        'season': 'race__season',
        'competition': 'race__season__competition',
        'seat': 'seat',
        'race': 'race'
    }
    filter_params = {}

    # kwarg is each param with custom filter

    for kwarg in key_in_filters.keys():
        value = locals().get(kwarg) # get the value of kwarg
        if value:
            key = key_in_filters.get(kwarg) # the key of filter is the value of kwarg in key_in_filter
            filter_params[key] = value
    filter_params.update(**extra_filters)


    results = Result.objects.filter(**filter_params)

    order_by_args = ('race__season', 'race__round') if not reverse_order else ('-race__season', '-race__round')

    results = results.order_by(*order_by_args)
    return results


def get_tuple_from_result(result):
    return ResultTuple(result.qualifying, result.finish, result.fastest_lap,
                       result.wildcard, result.race.alter_punctuation)


def get_results_tuples(seat=None, contender=None, team=None, race=None, season=None, competition=None,
                       results=None, skip_results_if_false=False, **extra_filters):

    # Result can be the only param passed to get_results_tuple.
    # If results=false, get_results will be calculate without params, return all results of all competitions.
    # If skip_results_if_false is True, results will be skipped but return ResultTuple structure.
    if not results and not skip_results_if_false:
        results = get_results(seat=seat, contender=contender, team=team, race=race,
                              season=season, competition=competition, **extra_filters)

    results = results.values_list('qualifying', 'finish', 'fastest_lap', 'wildcard', 'race__alter_punctuation')

    return results


@python_2_unicode_compatible
class Driver(models.Model):
    """ Main Driver Model. To combine with competitions (Contender) and competition/team (Seat) """
    last_name = models.CharField(max_length=50, verbose_name=_('last name'))
    first_name = models.CharField(max_length=25, verbose_name=_('first name'))
    year_of_birth = models.IntegerField(verbose_name=_('year of birth'))
    country = CountryField(verbose_name=_('country'))
    competitions = models.ManyToManyField('Competition', through='Contender', related_name='drivers',
                                          verbose_name=_('competitions'))

    def clean(self):
        if self.year_of_birth < 1900 or self.year_of_birth > 2099:
            raise ValidationError(_('Year_of_birth must be between 1900 and 2099'))
        super(Driver, self).clean()

    def __str__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')
        ordering = ['last_name', 'first_name']
        verbose_name = _('Driver')
        verbose_name_plural = _('Drivers')


@python_2_unicode_compatible
class Competition(AbstractRankModel):
    """ Competition model. Season, races, results... are grouped by competition """
    name = models.CharField(max_length=30, verbose_name=_('competition'), unique=True)
    full_name = models.CharField(max_length=100, unique=True, verbose_name=_('full name'))
    country = CountryField(null=True, blank=True, default=None, verbose_name=_('country'))
    slug = models.SlugField(null=True, blank=True, default=None)

    def get_team_rank(self, rank_type, **filters):
        return super(Competition, self).get_team_rank(rank_type=rank_type, competition=self, **filters)

    def get_stats_cls(self, contender):
        return contender

    def get_team_stats_cls(self, team):
        return team

    @property
    def stats_filter_kwargs(self):
        return {'competition': self}

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Competition, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Competition')
        verbose_name_plural = _('Competitions')


@python_2_unicode_compatible
class Contender(AbstractStatsModel):
    """ Contender are used to ranks or individual stats"""
    " Contender only can be related with teams of same competition "
    " If driver is related with same team in different competition, it is necessary to create new contender "
    driver = models.ForeignKey(Driver, related_name='career', verbose_name=_('driver'))
    competition = models.ForeignKey('Competition', related_name='contenders', verbose_name=_('competition'))
    teams = models.ManyToManyField('Team', through='Seat', related_name='contenders',
                                   verbose_name=_('teams'))

    def get_points(self, punctuation_config=None):
        seasons = Season.objects.filter(seats__contender=self).distinct()
        points = 0
        for season in seasons:
            contender_season = self.get_season(season)
            season_points = contender_season.get_points(punctuation_config=punctuation_config)
            points += season_points if season_points else 0
        return points

    def get_results(self, limit_races=None, **extra_filter):
        """ Return all results of team in season """
        return get_results(contender=self, **extra_filter)

    @property
    def teams_verbose(self):
        teams = self.teams
        return ', '.join([team.name for team in teams.all()]) if teams.count() else None

    def season_stats_cls(self, season):
        return ContenderSeason(contender=self, season=season)

    def __str__(self):
        return _(u'%(driver)s in %(competition)s') % {'driver': self.driver, 'competition': self.competition}

    class Meta:
        unique_together = ('driver', 'competition')
        ordering = ['competition__name', 'driver__last_name', 'driver__first_name']
        verbose_name = _('Contender')
        verbose_name_plural = _('Contenders')


@python_2_unicode_compatible
class Team(TeamStatsModel):
    """ Team model, unique if is the same in different competition """
    name = models.CharField(max_length=75, verbose_name=_('team'), unique=True)
    full_name = models.CharField(max_length=200, unique=True, verbose_name=_('full name'))
    competitions = models.ManyToManyField('Competition', related_name='teams', verbose_name=_('competitions'))
    country = CountryField(verbose_name=_('country'))

    def get_results(self, competition, **extra_filter):
        """ Return all results of team in season """
        return get_results(team=self, competition=competition, **extra_filter)

    def season_stats_cls(self, season):
        return TeamSeason.objects.get(season=season, team=self)

    def get_total_races(self, competition, **filters):
        return super(Team, self).get_total_races(competition=competition, **filters)

    def get_doubles_races(self, competition, **filters):
        return super(Team, self).get_doubles_races(competition=competition, **filters)

    def get_total_stats(self, competition, **filters):
        return super(Team, self).get_total_stats(competition=competition, **filters)


    @classmethod
    def bulk_copy(cls, teams_pk, season_pk):
        season_bulk_copy(cls=cls, cls_to_save=TeamSeason, pks=teams_pk, pks_name='team', season_pk=season_pk)

    @classmethod
    def check_list_in_season(cls, teams_pk, season_pk):
        teams_pk = list(map(int, teams_pk))
        teams = cls.objects.filter(pk__in=teams_pk)
        season = Season.objects.get(pk=season_pk)
        season_teams_pk = list(season.teams.values_list('pk', flat=True))

        not_exists = lr_diff(teams_pk, season_teams_pk)
        both_exists = lr_intr(teams_pk, season_teams_pk)

        not_exists_teams = [team for team in teams if team.pk in not_exists]
        both_exists_teams = [team for team in teams if team.pk in both_exists]

        can_save = True


        return {
            'not_exists': not_exists_teams,
            'both_exists': both_exists_teams,
            'can_save': can_save,
            'season_info': season
        }

    def get_points(self, competition, punctuation_config=None):
        seasons = Season.objects.filter(teams=self, competition=competition)
        points = 0
        for season in seasons:
            season_points = self.get_season(season).get_points(punctuation_config=punctuation_config)
            points += season_points if season_points else 0
        return points



    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')


@python_2_unicode_compatible
class Seat(models.Model):
    """ Seat is contender/team relation """
    " If a same contender drives to two teams in same season/competition, he will have many seats as driven teams "
    " e.g. Max Verstappen in 2016 (Seat 1: Toro Rosso, Seat 2: Red Bull) "
    team = models.ForeignKey('Team', related_name='seats', verbose_name=_('team'))
    contender = models.ForeignKey('Contender', related_name='seats', verbose_name=_('contender'))
    current = ExclusiveBooleanField(on='contender', default=False, verbose_name=_('current team'))
    seasons = models.ManyToManyField('Season', related_name='seats', blank=True, default=None,
                                     verbose_name=_('seasons'), through='SeatSeason')

    def clean(self):
        if self.contender.competition not in self.team.competitions.all():
            raise ValidationError(
                _("%(team)s is not a team of %(competition)s") %
                {'team': self.team, 'competition': self.contender.competition}
            )
        super(Seat, self).clean()

    @classmethod
    def bulk_copy(cls, seats_pk, season_pk):
        season_bulk_copy(cls=cls, cls_to_save=SeatSeason, pks=seats_pk, pks_name='seat', season_pk=season_pk)


    @classmethod
    def check_list_in_season(cls, seats_pk, season_pk):
        seats_pk = list(map(int, seats_pk))
        seats = cls.objects.filter(pk__in=seats_pk)

        season = Season.objects.get(pk=season_pk)
        season_teams_pk = list(season.teams.values_list('pk', flat=True))
        season_seats_pk = list(season.seats.values_list('pk', flat=True))

        not_exists = lr_diff(seats_pk, season_seats_pk)
        both_exists = lr_intr(seats_pk, season_seats_pk)

        not_exists_seats = []
        conditional_seats = []
        both_exists_seats = []

        for seat in seats:
            if seat.pk in both_exists:
                both_exists_seats.append(seat)
            elif seat.team.pk not in season_teams_pk:
                conditional_seats.append(seat)
            else:
                not_exists_seats.append(seat)

        can_save = True

        return {
            'not_exists': not_exists_seats,
            'both_exists': both_exists_seats,
            'conditional_exists': conditional_seats,
            'can_save': can_save,
            'season_info': season
        }

    def __str__(self):
        return _('%(driver)s in %(team)s/%(competition)s') \
               % {'driver': self.contender.driver, 'team': self.team,
                  'competition': self.contender.competition}

    class Meta:
        unique_together = ('team', 'contender')
        ordering = ['current', 'contender__driver__last_name', 'team']
        verbose_name = _('Seat')
        verbose_name_plural = _('Seats')


@python_2_unicode_compatible
class Circuit(models.Model):
    """ Circuit model. It can be in any competition, grand_prix or season """
    name = models.CharField(max_length=30, verbose_name=_('circuit'), unique=True)
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('city'))
    country = CountryField(verbose_name=_('country'))
    opened_in = models.IntegerField(verbose_name=_('opened in'))

    # @todo Add Clockwise and length
    def __str__(self):
        # @todo Add country name in __str__
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Circuit')
        verbose_name_plural = _('Circuits')


@python_2_unicode_compatible
class GrandPrix(models.Model):
    """ Grand Prix model """
    " default_circuit will be in future the default choice in circuit selector "
    name = models.CharField(max_length=30, verbose_name=_('grand prix'), unique=True)
    country = CountryField(null=True, blank=True, default=None, verbose_name=_('country'))
    first_held = models.IntegerField(null=True, blank=True, verbose_name=_('first held'))
    default_circuit = models.ForeignKey(Circuit, related_name='default_to_grands_prix', null=True,
                                        blank=True, default=None, verbose_name=_('default circuit'))
    competitions = models.ManyToManyField('Competition', related_name='grands_prix', default=None,
                                          verbose_name=_('competitions'))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Grand Prix')
        verbose_name_plural = _('Grands Prix')


@python_2_unicode_compatible
class Season(AbstractRankModel):
    """ Season model. The main model to restrict races, results and punctuation """
    year = models.IntegerField(verbose_name=_('year'))
    competition = models.ForeignKey(Competition, related_name='seasons', verbose_name=_('competition'))
    rounds = models.IntegerField(blank=True, null=True, default=None, verbose_name=_('rounds'))
    teams = models.ManyToManyField(Team, related_name='seasons', through='TeamSeason',
                                   verbose_name=_('teams'))
    punctuation = models.CharField(max_length=20, null=True, default=None, verbose_name=_('punctuation'))

    @property
    def stats_filter_kwargs(self):
        return {}

    @property
    def contenders(self):
        """ As season is related with seats, this method is a shorcut to get contenders """
        seats = [seat.pk for seat in self.seats.all()]
        return Contender.objects.filter(seats__pk__in=seats).distinct()

    def get_stats_cls(self, contender):
        return contender.get_season(self)

    def get_team_stats_cls(self, team):
        return TeamSeason.objects.get(season=self, team=team)

    def get_punctuation_config(self, punctuation_code=None):
        """ Getting the punctuation config. Chosen punctuation will be override temporarily by code kwarg """
        if not punctuation_code:
            punctuation_code = self.punctuation
        return get_punctuation_config(punctuation_code)

    def pending_races(self):
        """ Based on rounds field, return races count when race doesn't have any result """
        past_races = Race.objects.filter(season=self, results__pk__isnull=False).distinct().count()
        pending_races = (self.rounds - past_races)
        return pending_races

    def pending_points(self, punctuation_code=None):
        """ Return the maximum of available points taking into account the number of pending races"""
        # @todo fastest_lap and pole points are not counted
        if not punctuation_code:
            punctuation_code = self.punctuation
        punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
        max_score_by_race = sorted(punctuation_config.get('finish'), reverse=True)[0]
        pending_races = self.pending_races()
        return pending_races * max_score_by_race

    def leader_window(self, rank=None, punctuation_code=None):
        """ Minimum of current points a contestant must have to have any chance to be a champion.
        This is the subtraction of the points of the leader and the maximum of points that
        can be obtained in the remaining races."""
        pending_points = self.pending_points(punctuation_code=punctuation_code)
        leader = self.get_leader(rank=rank, punctuation_code=punctuation_code)
        return leader[0] - pending_points if leader else None

    def only_title_contenders(self, punctuation_code=None):
        """ They are only candidates for the title if they can reach the leader by adding all the pending points."""
        rank = self.points_rank(punctuation_code=punctuation_code)
        leader_window = self.leader_window(rank=rank, punctuation_code=punctuation_code)

        title_rank = []
        if leader_window:
            title_rank = [entry for entry in rank if entry[0] >= leader_window]
        return title_rank

    def has_champion(self, punctuation_code=None):
        """ If only exists one title contender, it has champion """
        leader_is_champions = False
        if len(self.only_title_contenders(punctuation_code=punctuation_code)) == 1:
            leader_is_champions = True
        return leader_is_champions

    def get_leader(self, rank=None, team=False, punctuation_code=None):
        """ Get driver leader or team leader """
        if not rank:
            if not punctuation_code:
                punctuation_code = self.punctuation
            rank = self.team_points_rank() if team else self.points_rank(punctuation_code=punctuation_code)
        return rank[0] if len(rank) else None

    @property
    def leader(self):
        """ get_leader(driver) property """
        return self.get_leader()

    @property
    def runner_up(self):
        """ Get the runner_up (driver) """
        rank = self.points_rank()
        return rank[1] if len(rank) > 1 else None

    @property
    def team_leader(self):
        """ get_leader(team) property """
        return self.get_leader(team=True)

    def __str__(self):
        return '/'.join((self.competition.name, str(self.year)))

    class Meta:
        unique_together = ('year', 'competition')
        ordering = ['competition__name', 'year']
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')


class SeatsSeason(Season):
    """ Aux proxy model to use in Admin for Season/Seat relation from Season """
    class Meta:
        proxy = True
        verbose_name = _('Seats by season')
        verbose_name_plural = _('Seats by season')


@python_2_unicode_compatible
class Race(models.Model):
    """ Race model. It can altered season punctuation (double or half) only in this race"""
    ALTER_PUNCTUATION = (
        ('double', _('Double')),
        ('half', _('Half'))
    )
    season = models.ForeignKey(Season, related_name='races', verbose_name=_('season'))
    round = models.IntegerField(verbose_name=_('round'))
    grand_prix = models.ForeignKey(GrandPrix, related_name='races', blank=True, null=True,
                                   default=None, verbose_name=_('grand prix'))
    circuit = models.ForeignKey(Circuit, related_name='races', blank=True, null=True,
                                default=None, verbose_name=_('circuit'))
    date = models.DateField(blank=True, null=True, default=None, verbose_name=_('date'))
    alter_punctuation = models.CharField(choices=ALTER_PUNCTUATION, null=True, blank=True,
                                         default=None, max_length=6, verbose_name=_('alter punctuation'))

    def _grandprix_exception(self):
        """ Grand Prix must be related with season competition """
        competition = self.season.competition
        if competition and self.grand_prix and competition not in self.grand_prix.competitions.all():
            return True
        else:
            return False

    def clean(self, *args, **kwargs):
        """ Validate round and grand_prix field """
        errors = {}
        season = getattr(self, 'season', None)
        if season:
            if self.round > self.season.rounds:
                errors['round'] = _('Max rounds in this season: %(rounds)d') % {'rounds': self.season.rounds}
            if self._grandprix_exception():
                errors['grand_prix'] = _("%(grand_prix)s is not a/an %(competition)s Grand Prix") \
                                       % {'grand_prix': self.grand_prix, 'competition': self.season.competition}
        if errors:
            raise ValidationError(errors)
        super(Race, self).clean()

    def get_result_seat(self, **kwargs):
        """ Return the first result that match with filter """
        results = self.results.filter(**kwargs)
        return results.first().seat if results.count() else None

    @property
    def pole(self):
        """ get_result_seat(pole) """
        return self.get_result_seat(qualifying=1)

    @property
    def winner(self):
        """ get_result_seat(winner) """
        return self.get_result_seat(finish=1)

    @property
    def fastest(self):
        """ get_result_seat(fastest) """
        return self.get_result_seat(fastest_lap=True)

    @classmethod
    def bulk_copy(cls, races_pk, season_pk):
        races = cls.objects.filter(pk__in=races_pk)
        season = Season.objects.get(pk=season_pk)

        season_rounds = season.rounds
        season_races = season.races.all()

        # As the value of race.round is limited from 1 to season.rounds value,
        # we will find the values available for the races that we are going to incorporate.
        season_rounds_range = list(range(1, season_rounds + 1))
        season_unavailable_rounds = list(season_races.values_list('round', flat=True))
        season_available_rounds = lr_diff(season_rounds_range, season_unavailable_rounds)

        for index, race in enumerate(races):
            # copy the grand_prix and circuit for each original race
            # and set round value between the available values
            cls.objects.create(
                round=season_available_rounds[index],
                season=season,
                grand_prix=race.grand_prix,
                circuit=race.circuit,
            )

    @classmethod
    def check_list_in_season(cls, races_pk, season_pk):
        # To consider that a race is included in a season, the grand prize has to be in it.
        races = cls.objects.filter(pk__in=races_pk)
        races_gp = list(races.values_list('grand_prix_id', flat=True))

        season = Season.objects.get(pk=season_pk)
        season_races = season.races.all()
        season_races_gp = list(season_races.values_list('grand_prix_id', flat=True))

        not_exists = lr_diff(races_gp, season_races_gp)
        both_exists = lr_intr(races_gp, season_races_gp)

        not_exists_races = [race for race in races if race.grand_prix_id in not_exists]
        both_exists_races = [race for race in races if race.grand_prix_id in both_exists]
        can_save = season.rounds >= (season_races.count() + len(not_exists_races))

        return {
            'not_exists': not_exists_races,
            'both_exists': both_exists_races,
            'can_save': can_save,
            'season_info': season
        }

    def __str__(self):
        race_str = '{season}-{round}'.format(season=self.season, round=self.round)
        if self.grand_prix:
            race_str += u'.{grand_prix}'.format(grand_prix=self.grand_prix)
        return race_str

    class Meta:
        unique_together = ('season', 'round')
        ordering = ['season', 'round']
        verbose_name = _('Race')
        verbose_name_plural = _('Races')


class SeatSeason(models.Model):
    """ Model created to validate restriction between both models """
    seat = models.ForeignKey('Seat', related_name='seasons_seat')
    season = models.ForeignKey('Season', related_name='seats_season')

    @staticmethod
    def get_seat_season_errors(seat, season):
        """ Check if seat is valid in current season competition """
        seat_competition = seat.contender.competition
        season_competition = season.competition
        errors = []
        if seat_competition != season_competition:
            errors.append(
                _('%(season)s is not a/an %(competition)s season')
                % {'season': season, 'competition': seat_competition}
            )
        return errors

    @staticmethod
    def get_seat_team_season_error(team, season):
        """ Check if team is valid in current season """
        " Team must be related with season before of save Seat/Season rel "
        errors = []
        if season.pk:
            season_teams = [season_team.pk for season_team in season.teams.all()]
            if team.pk not in season_teams:
                errors.append(
                    _('%(team)s is not a team of %(season)s') % {'team': team, 'season': season}
                )
        return errors

    def clean(self, *args, **kwargs):
        """ Check validation """
        seat = self.seat
        season = self.season
        errors = []
        errors.extend(self.get_seat_season_errors(seat, season))
        errors.extend(self.get_seat_team_season_error(seat.team, season))
        if errors:
            raise ValidationError(errors)
        super(SeatSeason, self).clean()

    def save(self, *args, **kwargs):
        """ Force to validate before of save """
        self.clean()
        super(SeatSeason, self).save(*args, **kwargs)

    class Meta:
        auto_created = True
        db_table = 'driver27_seat_seasons'


def seat_seasons(sender, instance, action, pk_set, **kwargs):  #noqa
    """ Signal in DriverCompetitionTeam.seasons to avoid seasons which not is in competition """
    if action == 'pre_add':
        errors = []
        for pk in list(pk_set):
            season = Season.objects.get(pk=pk)
            errors.extend(SeatSeason.get_seat_season_errors(instance, season))
            errors.extend(SeatSeason.get_seat_team_season_error(instance.team, season))
        if errors:
            raise ValidationError(errors)

m2m_changed.connect(seat_seasons, sender=SeatSeason)


@python_2_unicode_compatible
class TeamSeason(TeamStatsModel):
    """ TeamSeason model, only for validation although it is saved in DB"""
    season = models.ForeignKey('Season', related_name='teams_season', verbose_name=_('season'))
    team = models.ForeignKey('Team', related_name='seasons_team', verbose_name=_('team'))
    sponsor_name = models.CharField(max_length=75, null=True, blank=True, default=None,
                                    verbose_name=_('sponsor name'))

    @property
    def stats_filter_kwargs(self):
        return {'season': self.season, 'team': self.team}

    def get_results(self, limit_races=None, **extra_filter):
        """ Return all results of team in season """
        results_filter = self.stats_filter_kwargs
        return get_results(limit_races=limit_races, **dict(results_filter, **extra_filter))

    def get_points(self, limit_races=None, punctuation_config=None):
        """ Get points. Can be limited. Punctuation config will be overwrite temporarily"""

        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races)
        else:
            points_list = []
            results = self.get_results(limit_races=limit_races)
            # Result can be the only param passed to get_results_tuple.
            # If results=false, get_results will be calculate without params, return all results of all competitions.
            # If skip_results_if_false is True, results will be skipped but return ResultTuple structure.
            for result in get_results_tuples(results=results, skip_results_if_false=True):
                result_tuple = ResultTuple(*result)
                points = PointsCalculator(punctuation_config).calculator(result_tuple, skip_wildcard=True)
                if points:
                    points_list.append(points)
        return sum(points_list)

    def get_positions_list(self, limit_races=None):
        """ Return a list with the count of each 20 first positions """
        results = self.get_results(limit_races=limit_races)
        finished = results.values_list('finish', flat=True)
        last_position = 20
        positions = []
        for x in range(1, last_position+1):
            position_count = len([finish for finish in finished if finish==x])
            positions.append(position_count)
        return positions

    def get_positions_str(self, position_list=None, limit_races=None):
        """ Return a str with position_list to order """
        " Each list item will be filled to zeros until get three digits e.g. 1 => 001, 12 => 012 "
        if not position_list:
            position_list = self.get_positions_list(limit_races=limit_races)
        positions_str = ''.join([str(x).zfill(3) for x in position_list])
        return positions_str

    def clean(self, *args, **kwargs):
        """ Check if team participate in competition """
        if hasattr(self, 'team') and hasattr(self, 'season'):
            team = self.team
            team_competitions = [competition.pk for competition in team.competitions.all()]
            if self.season.competition.pk not in team_competitions:
                raise ValidationError(
                    _('Team %(team)s doesn\'t participate in %(competition)s')
                    % {'team': self.team, 'competition': self.season.competition}
                )
        super(TeamSeason, self).clean()

    @classmethod
    def delete_seat_exception(cls, team, season):
        """ Force IntegrityError when delete a team with seats in season """
        if cls.check_delete_seat_restriction(team=team, season=season):
            raise IntegrityError('You cannot delete a team with seats in this season.'
                                 'Delete seats before')

    @staticmethod
    def check_delete_seat_restriction(team, season):
        seats_count = SeatSeason.objects.filter(seat__team=team, season=season).count()
        return bool(seats_count)
        # return {'team': _('Seats with %(team)s exists in this season. Delete seats before.' % {'team': team})}

    def __str__(self):
        str_team = self.team.name
        if self.sponsor_name:
            str_team = self.sponsor_name
        return '{team} in {season}'.format(team=str_team, season=self.season)

    class Meta:
        unique_together = ('season', 'team')
        verbose_name = _('Team Season')
        verbose_name_plural = _('Teams Season')


@python_2_unicode_compatible
class Result(models.Model):
    """ Result model """
    race = models.ForeignKey(Race, related_name='results', verbose_name=_('race'))
    seat = models.ForeignKey(Seat, related_name='results', verbose_name=_('seat'))
    qualifying = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None, verbose_name=_('qualifying'))
    finish = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None, verbose_name=_('finish'))
    fastest_lap = ExclusiveBooleanField(on='race', default=False, verbose_name=_('fastest lap'))
    retired = models.BooleanField(default=False, verbose_name=_('retired'))
    wildcard = models.BooleanField(default=False, verbose_name=_('wildcard'))
    comment = models.CharField(max_length=250, blank=True, null=True, default=None, verbose_name=_('comment'))
    points = models.IntegerField(default=0, blank=True, null=True, verbose_name=_('points'))

    def save(self, *args, **kwargs):
        self.points = self.get_points()
        super(Result, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        # seat_errors = []
        if self.seat.team not in self.race.season.teams.all():
            # seat_errors.append(ValidationError(_('Team is not in current season'), code='invalid'))
            raise ValidationError({'seat': _('Team (seat) is not in current season')})
        if self.seat not in self.race.season.seats.all():
            # seat_errors.append(ValidationError(_('Seat is not in current season'), code='invalid'))
            raise ValidationError({'seat': _('Seat is not in current season')})
        # if seat_errors:
        #     seat_errors.append(ValidationError(_('Invalid Seat in this race.'), code='invalid'))
        #     raise ValidationError(seat_errors, code='invalid')

        super(Result, self).clean()

    @property
    def driver(self):
        return self.seat.contender.driver

    @property
    def team(self):
        return self.seat.team

    def points_calculator(self, punctuation_config):
        result_tuple = get_tuple_from_result(self)
        return PointsCalculator(punctuation_config).calculator(result_tuple)

    def get_points(self):
        """ Return points based on season scoring """
        punctuation_config = self.race.season.get_punctuation_config()
        return self.points_calculator(punctuation_config)

    def __str__(self):
        string = '{seat} ({race})'.format(seat=self.seat, race=self.race)
        if self.finish:
            string += ' - {finish}º'.format(finish=self.finish)
        else:
            string += ' - ' + _('OUT')
        return string

    class Meta:
        unique_together = ('race', 'seat')
        ordering = ['race__season', 'race__round', 'finish', 'qualifying']
        verbose_name = _('Result')
        verbose_name_plural = _('Results')


class ContenderSeason(object):
    """ ContenderSeason is not a model. Only for validation and ranks"""
    contender = None
    season = None
    teams = None
    contender_teams = None
    teams_verbose = None

    def __init__(self, contender, season):
        if not isinstance(contender, Contender) or not isinstance(season, Season):
            raise ValidationError(_('contender is not a Contender or/and season is not a Season'))
        self.contender = contender
        self.season = season
        self.seats = Seat.objects.filter(contender__pk=self.contender.pk, seasons__pk=self.season.pk)
        self.teams = Team.objects.filter(seats__in=self.seats)
        self.teams_verbose = ', '.join([team.name for team in self.teams])



    def get_results(self, limit_races=None, **extra_filter):
        """ Return results. Can be limited."""
        return get_results(contender=self.contender, season=self.season, limit_races=limit_races, **extra_filter)

    def get_reverse_results(self, limit_races=None, **extra_filter):
        return self.get_results(limit_races=limit_races, reverse_order=True, **extra_filter)

    def get_streak(self, **filters):
        results = self.get_reverse_results()
        counter = 0
        return Streak(results=results).run(filters)

    def get_stats(self, **filters):
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    def get_saved_points(self, limit_races=None):
        results = self.get_results(limit_races=limit_races)
        points = results.values_list('points', flat=True)
        return [point for point in points if point]

    def get_points(self, limit_races=None, punctuation_config=None):
        """ Get points. Can be limited. Punctuation config will be overwrite temporarily"""

        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races)
        else:
            points_list = []
            results = self.get_results(limit_races=limit_races)
            # Result can be the only param passed to get_results_tuple.
            # If results=false, get_results will be calculate without params, return all results of all competitions.
            # If skip_results_if_false is True, results will be skipped but return ResultTuple structure.
            for result in get_results_tuples(results=results, skip_results_if_false=True):
                result_tuple = ResultTuple(*result)
                points = PointsCalculator(punctuation_config).calculator(result_tuple)
                if points:
                    points_list.append(points)
        return sum(points_list)
        
    def get_positions_list(self, limit_races=None):
        """ Return a list with the count of each 20 first positions """
        results = self.get_results(limit_races=limit_races)
        finished = results.values_list('finish', flat=True)
        last_position = 20
        positions = []
        for x in range(1, last_position+1):
            position_count = len([finish for finish in finished if finish==x])
            positions.append(position_count)
        return positions

    def get_positions_str(self, position_list=None, limit_races=None):
        """ Return a str with position_list to order """
        " Each list item will be filled to zeros until get three digits e.g. 1 => 001, 12 => 012 "
        if not position_list:
            position_list = self.get_positions_list(limit_races=limit_races)
        positions_str = ''.join([str(x).zfill(3) for x in position_list])
        return positions_str


@receiver(pre_save)
def pre_save_handler(sender, instance, *args, **kwargs):
    """ Force full_clean in each model to validation """
    model_list = (Driver, Team, Competition, Contender, Seat, Circuit,
                  GrandPrix, Race, Season, Result, SeatSeason, TeamSeason)
    if not isinstance(instance, model_list):
        return
    instance.full_clean()


@receiver(pre_delete, sender=TeamSeason)
def pre_delete_team_season(sender, instance, *args, **kwargs):
    """ Force exception before of delete team in season when exists dependent seats """
    team = instance.team
    season = instance.season
    TeamSeason.delete_seat_exception(team=team, season=season)
