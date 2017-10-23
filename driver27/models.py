# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from django_countries.fields import CountryField
from slugify import slugify
from swapfield.fields import SwapIntegerField

from . import lr_intr, lr_diff
from .points_calculator import PointsCalculator
from .punctuation import get_punctuation_config
from .rank import AbstractRankModel
from .stats import AbstractStreakModel, AbstractStatsModel, TeamStatsModel, StatsByCompetitionModel, SeasonStatsModel

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .common import DRIVER27_NAMESPACE

ResultTuple = namedtuple('ResultTuple',
                         'qualifying finish fastest_lap wildcard retired race_id circuit grand_prix country competition year ' \
                         'round alter_punctuation points')


def get_tuples_from_results(results):
    return [get_tuple_from_result(result) for result in results]


def get_tuple_from_result(result, **kwargs):
    result_kwargs = {
        'qualifying': result.qualifying,
        'finish': result.finish,
        'fastest_lap': result.is_fastest,
        'wildcard': result.wildcard,
        'retired': result.retired,
        'race_id': result.race_id,
        'circuit': result.race.circuit,
        'grand_prix': result.race.grand_prix,
        'country': getattr(result.race.grand_prix, 'country', None),
        'competition': result.race.season.competition,
        'year': result.race.season.year,
        'round': result.race.round,
        'alter_punctuation': result.race.alter_punctuation,
        'points': result.points
    }

    result_kwargs.update(**kwargs)

    return ResultTuple(**result_kwargs)


@python_2_unicode_compatible
class Driver(StatsByCompetitionModel):
    """ Main Driver Model. To combine with competitions (Contender) and competition/team (Seat) """
    last_name = models.CharField(max_length=50, verbose_name=_('last name'))
    first_name = models.CharField(max_length=25, verbose_name=_('first name'))
    year_of_birth = models.IntegerField(verbose_name=_('year of birth'), null=True, blank=True)
    country = CountryField(verbose_name=_('country'), null=True, blank=True)
    teams = models.ManyToManyField('Team', through='Seat', related_name='drivers', verbose_name=_('teams'))

    def get_absolute_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'global:driver-profile'])
        return reverse(URL, kwargs = {'driver_id': self.pk})

    @property
    def result_filter_kwargs(self):
        return {}

    @property
    def races(self):
        """ Races with at least one result of this driver """
        return Race.objects.filter(results__seat__driver=self).distinct()

    @property
    def seasons(self):
        """ Season with at least one result of this driver """
        return Season.objects.filter(races__in=self.races.all()).distinct()

    @property
    def competitions(self):
        """ Competition with at least one result of this driver """
        return Competition.objects.filter(seasons__in=self.seasons.all()).distinct()

    @property
    def is_active(self):
        """ A driver is active when has at least one result in last year registered in seasons """
        seasons_ordered_by_desc_year = Season.objects.order_by('-year')
        if seasons_ordered_by_desc_year.count():
            last_year = seasons_ordered_by_desc_year[0].year
            return Result.wizard(driver=self, race__season__year=last_year).count()
        else:
            return True

    def get_summary_points(self, append_to_summary=None, **kwargs):
        kwargs.pop('exclude_position', False)
        punctuation_config = kwargs.pop('punctuation_config', None)
        positions_count_list = self.get_positions_count_list(**kwargs)
        positions_count_str = self.get_positions_count_str(position_list=positions_count_list)
        summary_points = {
            'teams': self.teams_verbose,
            'points': self.get_points(punctuation_config=punctuation_config, **kwargs),
            'pos_list': positions_count_list,
            'pos_str': positions_count_str
        }
        if append_to_summary is not None:
            summary_points.update(**append_to_summary)
        return summary_points

    def _teams_verbose(self, teams):
        return ', '.join([team.name for team in teams])

    @property
    def teams_verbose(self):
        """ A str separated with commas with teams names """
        return self._teams_verbose(self.teams.all())

    def get_results(self, limit_races=None, **extra_filter):
        """ Result of driver """
        return Result.wizard(driver=self, limit_races=limit_races, **extra_filter)

    def get_saved_points(self, limit_races=None, **kwargs):
        """ List of result.points from results of driver """
        results = self.get_results(limit_races=limit_races, **kwargs)
        points = results.values_list('points', flat=True)
        return [point for point in points if point]


    def season_stats_cls(self, season):
        """ Return the instance with driver-season pair """
        return ContenderSeason(driver=self, season=season)

    def get_points_by_season(self, season, **kwargs):
        """
        Return points summary of a driver in a season
        """
        summary_points = self.season_stats_cls(season=season).get_summary_points(**kwargs)
        return summary_points

    def get_points_by_seasons(self, **kwargs):
        """
        Return points summary of each season of driver

        """
        kwargs.pop('season', None)
        seasons = self.seasons.all()
        return [self.get_points_by_season(season=season, **kwargs) for season in seasons]

    def __str__(self):
        return u', '.join((self.last_name, self.first_name))

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

    def get_absolute_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'competition:view'])
        return reverse(URL, kwargs = {'competition_slug': self.slug})

    @property
    def drivers(self):
        """ Queryset of driver with at least one result in a race of this competition """
        return Driver.objects.filter(seats__results__race__season__competition=self).distinct()

    def get_team_rank(self, rank_type, **filters):
        return super(Competition, self).get_team_rank(rank_type=rank_type, competition=self, **filters)

    def get_stats_cls(self, driver):
        return driver

    def get_team_stats_cls(self, team):
        return team

    @property
    def stats_filter_kwargs(self):
        return {'competition': self}

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Competition, self).save(*args, **kwargs)

    def __str__(self):
        return u'{name}'.format(name=self.name)

    class Meta:
        ordering = ['name']
        verbose_name = _('Competition')
        verbose_name_plural = _('Competitions')


class CompetitionTeam(models.Model):
    team = models.ForeignKey('Team', related_name='periods', verbose_name=_('team'))
    competition = models.ForeignKey('Competition', related_name='periods', verbose_name=_('competition'))
    from_year = models.IntegerField(blank=True, null=True, default=None)
    until_year = models.IntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('team', 'competition', 'from_year', 'until_year')


@python_2_unicode_compatible
class Team(TeamStatsModel, StatsByCompetitionModel):
    """ Team model, unique if is the same in different competition """
    name = models.CharField(max_length=75, verbose_name=_('team'), unique=True)
    full_name = models.CharField(max_length=200, unique=True, verbose_name=_('full name'))
    competitions = models.ManyToManyField('Competition', through='CompetitionTeam', related_name='teams',
                                          verbose_name=_('competitions'))
    country = CountryField(verbose_name=_('country'), blank=True, null=True)

    def get_absolute_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'global:team-profile'])
        return reverse(URL, kwargs = {'team_id': self.pk})

    def _races(self, competition=None, **kwargs):
        """
        Return a races of a team
        With param competition, the filter is different
        """
        kwargs.update(**{'results__seat__team': self})
        if competition is not None:
            kwargs.update(**{'season__competition': competition})
        return Race.objects.filter(**kwargs).distinct()

    @property
    def races(self):
        return self._races().distinct()

    @property
    def seasons(self):
        return Season.objects.filter(races__in=self.races.all()).distinct()

    def get_results(self, competition=None, **extra_filter):
        """ Return results of a team """
        return Result.wizard(team=self, competition=competition, **extra_filter)

    def get_results_by_race(self, race):
        """ Shorcut for return results of a team in a race"""
        return self.get_results(race=race)

    def get_drivers_by_race(self, race):
        """ Shorcut for return drivers of a team in a race"""
        results = self.get_results_by_race(race=race)
        return list(set([result.seat.driver for result in results]))

    def get_drivers_by_race_str(self, race):
        """ Str with drivers name in a race """
        return ' + '.join(sorted(['{driver}'.format(driver=driver) for driver in self.get_drivers_by_race(race)]))


    def get_total_races(self, competition=None, **filters):
        return super(Team, self).get_total_races(competition=competition, **filters)

    def get_doubles_races(self, competition=None, **filters):
        return super(Team, self).get_doubles_races(competition=competition, **filters)

    def get_total_stats(self, competition=None, **filters):
        return super(Team, self).get_total_stats(competition=competition, **filters)

    def season_stats_cls(self, season):
        return TeamSeason.objects.get(season=season, team=self)

    def get_summary_points(self, append_to_summary=None, **kwargs):
        kwargs.pop('exclude_position', False)
        punctuation_config = kwargs.pop('punctuation_config', None)
        positions_count_list = self.get_positions_count_list(**kwargs)
        positions_count_str = self.get_positions_count_str(position_list=positions_count_list)
        summary_points = {
            'points': self.get_points(punctuation_config=punctuation_config, **kwargs),
            'pos_list': positions_count_list,
            'pos_str': positions_count_str
        }

        if append_to_summary is not None:
            summary_points.update(**append_to_summary)
        return summary_points

    def get_points_by_season(self, season, append_team=False, **kwargs):
        summary_points = self.season_stats_cls(season=season).get_summary_points(**kwargs)
        if append_team:
            summary_points['team'] = self
        return summary_points

    def get_points_by_seasons(self, append_team=False, **kwargs):
        kwargs.pop('season', None)
        seasons = self.seasons.all()
        return [self.get_points_by_season(season=season, append_team=append_team, **kwargs) for season in seasons]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')


@python_2_unicode_compatible
class SeatPeriod(models.Model):
    seat = models.ForeignKey('Seat', related_name='periods')
    from_year = models.IntegerField(blank=True, null=True, default=None)
    until_year = models.IntegerField(blank=True, null=True, default=None)

    def __str__(self):
        return_text = '{seat}'.format(seat=self.seat)
        if self.from_year:
            return_text += ' from {from_year}'.format(from_year=self.from_year)
        if self.until_year:
            return_text += ' until {until_year}'.format(until_year=self.until_year)
        return return_text


@python_2_unicode_compatible
class Seat(models.Model):
    """ Seat is contender/team relation """
    " If a same contender drives to two teams in same season/competition, he will have many seats as driven teams "
    " e.g. Max Verstappen in 2016 (Seat 1: Toro Rosso, Seat 2: Red Bull) "
    team = models.ForeignKey('Team', related_name='seats', verbose_name=_('team'))
    driver = models.ForeignKey('Driver', related_name='seats', verbose_name=_('driver'), default=None, null=True)

    def __str__(self):
        return _(u'%(driver)s in %(team)s') \
               % {'driver': self.driver, 'team': self.team}

    class Meta:
        unique_together = ('team', 'driver',)
        ordering = ['driver__last_name', 'team']
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
    punctuation = models.CharField(max_length=20, null=True, default=None, verbose_name=_('punctuation'))

    def get_params_url(self):
        return {'competition_slug': self.competition.slug, 'year': self.year}

    def get_absolute_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'season:view'])
        return reverse(URL, kwargs=self.get_params_url())

    def get_races_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'season:race-list'])
        return reverse(URL, kwargs=self.get_params_url())


    @property
    def stats_filter_kwargs(self):
        return {'season': self}

    def get_results(self, kwargs=None):
        cache_str = 'season_results_{pk}'.format(pk=self.pk)
        cache_results = cache.get(cache_str)

        if cache_results:
            results = cache_results
        else:
            results = Result.wizard(season=self)
            cache.set(cache_str, results)
        return results

    def get_results_list(self, element='driver', kwargs=None):
        cache_str = 'season_results_{pk}_{element}'.format(pk=self.pk, element=element)
        cache_results_list = cache.get(cache_str)

        if cache_results_list:
            entries = cache_results_list
        else:
            results = self.get_results()
            entries = {}
            for result in results:
                key = getattr(result, element)
                if key not in entries:
                    entries[key] = []
                entries[key].append(result)
            cache.set(cache_str, entries)
        return entries

    def get_results_by_drivers(self):
        return self.get_results_list('driver')


    def get_results_by_teams(self):
        return self.get_results_list('team')

    @property
    def drivers(self):
        """ As season is related with seats, this method is a shorcut to get drivers """
        return Driver.objects.filter(seats__results__race__season=self).distinct()

    @property
    def teams(self):
        """ As season is related with seats, this method is a shorcut to get teams """
        return Team.objects.filter(seats__results__race__season=self).distinct()

    def get_positions_draw(self):
        points_rank = self.points_rank()
        position_draw = []
        for entry in points_rank:
            contender_season = ContenderSeason(driver=entry['driver'], season=self)
            position_draw.append(
                {'pos_list': contender_season.get_positions_in_row(),
                 'driver': entry['driver'],
                 'teams': contender_season.teams_verbose,
                 'pos_str': ''
                 }
            )
        return position_draw

    def _abstract_seats(self, exclude=False):
        seat_filter = {'team__competitions__seasons': self}
        seats = Seat.objects.filter(**seat_filter)
        filter_or_exclude = 'filter' if not exclude else 'exclude'
        return getattr(seats, filter_or_exclude)(

            Q(periods__from_year__lte=self.year) | Q(periods__from_year__isnull=True),
            Q(periods__until_year__gte=self.year) | Q(periods__until_year__isnull=True)
        ).distinct()

    @property
    def seats(self):
        return self._abstract_seats()

    @property
    def no_seats(self):
        return self._abstract_seats(exclude=True)

    def get_stats_cls(self, driver):
        return driver.get_season(self)

    def get_team_stats_cls(self, team):
        team_season, created = TeamSeason.objects.get_or_create(season=self, team=team)
        return team_season

    def get_punctuation_config(self, punctuation_code=None):
        """ Getting the punctuation config. Chosen punctuation will be override temporarily by code kwarg """
        if not punctuation_code:
            punctuation_code = self.punctuation
        return get_punctuation_config(punctuation_code)

    def past_or_pending_races(self, past=True):
        filter_no_results = {'results__pk__isnull': True}
        races = self.races
        if past:
            races = races.exclude(**filter_no_results)
        else:
            races = races.filter(**filter_no_results)
        return races.distinct()

    @property
    def pending_races(self):
        return self.past_or_pending_races(past=False)

    @property
    def past_races(self):
        return self.past_or_pending_races(past=True)

    @property
    def num_pending_races(self):
        expected_pending_races = races_no_results = self.pending_races.count()
        season_rounds = self.rounds
        if season_rounds:
            expected_pending_races = self.rounds - races_no_results
        if races_no_results > expected_pending_races:
            races_no_results = expected_pending_races
        return races_no_results

    def pending_points(self, punctuation_code=None):
        """ Return the maximum of available points taking into account the number of pending races"""
        # @todo fastest_lap and pole points are not counted
        if not punctuation_code:
            punctuation_code = self.punctuation
        punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
        max_points = 0

        for race in self.pending_races.all():
            # max_result = Result(finish=1, qualifying=1, race=race)
            # @todo fastest_car modify tuple behavior
            max_result = Result(finish=1, qualifying=1, race=race)
            max_tuple = get_tuple_from_result(max_result, fastest_lap=True)
            max_points += PointsCalculator(punctuation_config=punctuation_config).calculator(
                max_tuple
            )
        return max_points

    def leader_window(self, rank=None, punctuation_code=None):
        """ Minimum of current points a contestant must have to have any chance to be a champion.
        This is the subtraction of the points of the leader and the maximum of points that
        can be obtained in the remaining races."""
        punctuation_code_dict = {'punctuation_code': punctuation_code}
        pending_points = self.pending_points(**punctuation_code_dict)
        leader = self.get_leader(rank=rank, **punctuation_code_dict)
        return leader['points'] - pending_points if leader else None

    def only_title_contenders(self, punctuation_code=None):
        """ They are only candidates for the title if they can reach the leader by adding all the pending points."""
        punctuation_code_dict = {'punctuation_code': punctuation_code}
        rank = self.points_rank(**punctuation_code_dict)
        leader_window = self.leader_window(rank=rank, **punctuation_code_dict)

        title_rank = []
        if leader_window is not None:  # Can be zero
            title_rank = [entry for entry in rank if entry['points'] >= leader_window]
        return title_rank

    def the_champion(self, punctuation_code=None):
        title_contenders = self.only_title_contenders(punctuation_code=punctuation_code)
        if len(title_contenders) == 1:
            return title_contenders[0]
        return None

    def has_champion(self, punctuation_code=None):
        """ If only exists one title contender, it has champion """
        return self.the_champion(punctuation_code=punctuation_code) is not None

    def get_leader(self, rank=None, team=False, punctuation_code=None):
        """ Get driver leader or team leader """
        if not rank:
            # if not punctuation_code:
            #     punctuation_code = self.punctuation
            punctuation_code_dict = {'punctuation_code': punctuation_code}
            rank_method = 'team_points_rank' if team else 'points_rank'
            rank = getattr(self, rank_method)(**punctuation_code_dict)
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
        return '{competition}/{year}'.format(competition=self.competition, year=self.year)

    class Meta:
        unique_together = ('year', 'competition')
        ordering = ['year', 'competition__name', ]
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
    fastest_car = models.ForeignKey(Seat, related_name='fastest_in', blank=True, null=True, default=None,
                                    on_delete=models.SET_NULL)


    def get_absolute_url(self):
        URL = ':'.join([DRIVER27_NAMESPACE, 'season:race-view'])
        season = self.season
        slug = season.competition.slug
        year = season.year
        return reverse(URL, kwargs = {'competition_slug': slug, 'year': year, 'race_id': self.round})

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

    def _abstract_seats(self, exclude=False):
        seat_filter = {'team__competitions__seasons__races': self}
        seat_exclude = {'driver__seats__results__race': self}
        seats = Seat.objects.filter(**seat_filter)
        if exclude:
            seats = seats.exclude(**seat_exclude)

        return seats.filter(
            Q(periods__from_year__lte=self.season.year) | Q(periods__from_year__isnull=True),
            Q(periods__until_year__gte=self.season.year) | Q(periods__until_year__isnull=True)
        ).distinct()

    @property
    def seats(self):
        return self._abstract_seats()

    @property
    def drivers(self):
        return Driver.objects.filter(seats__in=self.seats)

    @property
    def teams(self):
        return Team.objects.filter(seats__in=self.seats).distinct()

    @property
    def no_seats(self):
        return self._abstract_seats(exclude=True)

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
        return self.fastest_car

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


@python_2_unicode_compatible
class TeamSeason(TeamStatsModel, SeasonStatsModel):
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
        return Result.wizard(limit_races=limit_races, **dict(results_filter, **extra_filter))

    def get_points_list(self, limit_races=None, punctuation_config=None, **kwargs):
        points_to_rank = kwargs.pop('points_to_rank', None)
        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races, **kwargs)
        else:
            points_list = []
            if points_to_rank:
                results = self.season.get_results_list('team')[self.team]
            else:
                results = self.get_results(limit_races=limit_races, **kwargs)

            for result_tuple in get_tuples_from_results(results=results):
                points = PointsCalculator(punctuation_config).calculator(result_tuple, skip_wildcard=True)
                if points: points_list.append(points)
        return points_list

    def get_points(self, limit_races=None, punctuation_config=None, **kwargs):
        """ Get points. Can be limited. Punctuation config will be overwrite temporarily"""
        points_list = self.get_points_list(limit_races=limit_races, punctuation_config=punctuation_config, **kwargs)

        return sum(points_list)

    def get_name_in_season(self):
        str_team = self.team.name
        if self.sponsor_name:
            str_team = self.sponsor_name
        return str_team

    def _summary_season(self, exclude_position=False):

        summary_season = {
            'season': self.season,
            'competition': self.season.competition,
            'year': self.season.year
        }

        if not exclude_position:
            summary_season['pos'] = self.get_points_position()
        return summary_season

    def get_summary_stats(self, records_list=None, append_points=False, **kwargs):
        """
        Return multiple records (or only one) record in season

        """
        exclude_position = kwargs.pop('exclude_position', False)
        summary_stats = self._summary_season(exclude_position)
        season = summary_stats.get('season')
        seats = season.seats.filter(team=self.team)

        summary_stats.update(
            seats=seats,
            stats=self.team.get_stats_list(records_list=records_list, append_points=append_points, season=season, **kwargs)
        )

        return summary_stats


    def get_points_position(self):

        """
        Return position in season rank

        """
        return self._points_position('team_points_rank', 'team')

    def __str__(self):
        str_team = self.get_name_in_season()
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
    qualifying = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None,
                                  verbose_name=_('qualifying'))
    finish = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None, verbose_name=_('finish'))
    # fastest_lap = ExclusiveBooleanField(on='race', default=False, verbose_name=_('fastest lap'))
    retired = models.BooleanField(default=False, verbose_name=_('retired'))
    wildcard = models.BooleanField(default=False, verbose_name=_('wildcard'))
    comment = models.CharField(max_length=250, blank=True, null=True, default=None, verbose_name=_('comment'))
    points = models.IntegerField(default=0, blank=True, null=True, verbose_name=_('points'))

    @classmethod
    def wizard(cls, seat=None, driver=None, team=None,
               race=None, season=None, competition=None,
               grand_prix=None, circuit=None,
               limit_races=None,
               reverse_order=False,
               **extra_filters):
        key_in_filters = {
            'limit_races': 'race__round__lte',
            'driver': 'seat__driver',
            'team': 'seat__team',
            'season': 'race__season',
            'competition': 'race__season__competition',
            'seat': 'seat',
            'race': 'race',
            'grand_prix': 'race__grand_prix',
            'circuit': 'race__circuit'
        }
        filter_params = {}

        # kwarg is each param with custom filter

        for kwarg in key_in_filters.keys():
            value = locals().get(kwarg)  # get the value of kwarg
            if value:
                key = key_in_filters.get(kwarg)  # the key of filter is the value of kwarg in key_in_filter
                filter_params[key] = value
        filter_params.update(**extra_filters)

        results = cls.objects.filter(**filter_params)

        order_by_args = ('race__season__year', 'race__date', 'race__season__pk', 'race__round') \
            if not reverse_order else ('-race__season__year', '-race__date', '-race__season__pk', '-race__round')

        results = results.order_by(*order_by_args)
        return results

    def _validate_seat(self):
        errors = {'seat': []}
        if not self.race.season.competition.teams.filter(pk=self.seat.team.pk).exists():
            errors['seat'].append('Team not in Competition')
        if Result.wizard(driver=self.seat.driver, race=self.race).exclude(pk=self.pk).exists():
            errors['seat'].append('Exists a result with the same driver in this race (different Seat)')
        if not self.race.season.seats.filter(pk=self.seat.pk).exists():
            errors['seat'].append('{seat} is not valid in {season_year}'.format(seat=self.seat,
                                                                                season_year=self.race.season.year))
        if errors['seat']:
            raise ValidationError(errors)

    def clean(self):
        self._validate_seat()
        super(Result, self).clean()

    def save(self, *args, **kwargs):
        self._validate_seat()
        self.points = self.get_points()
        super(Result, self).save(*args, **kwargs)
        cache.clear()

    @property
    def driver(self):
        return self.seat.driver

    @property
    def team(self):
        return self.seat.team

    @property
    def is_fastest(self):
        try:
            return self.race.fastest_car.pk == self.seat.pk
        except AttributeError:
            return False

    def points_calculator(self, punctuation_config):
        result_tuple = get_tuple_from_result(self)
        calculator = PointsCalculator(punctuation_config).calculator(result_tuple)
        return calculator

    def get_points(self):
        """ Return points based on season scoring """
        punctuation_config = self.race.season.get_punctuation_config()
        return self.points_calculator(punctuation_config)

    def __str__(self):
        string = '{seat} ({race})'.format(seat=self.seat, race=self.race)
        if self.finish:
            string += ' - {finish}º'.format(finish=self.finish)
        else:
            string += ' - ' + _('DNF')
        return string

    class Meta:
        unique_together = ('race', 'seat')
        ordering = ['race__season', 'race__round', 'finish', 'qualifying']
        verbose_name = _('Result')
        verbose_name_plural = _('Results')


class ContenderSeason(AbstractStreakModel, SeasonStatsModel):
    """ ContenderSeason is not a model. Only for validation and ranks"""

    driver = None
    season = None
    teams = None
    contender_teams = None
    teams_verbose = None

    def __init__(self, driver, season):
        self.driver = driver
        self.season = season
        self.seats = Seat.objects.filter(driver__pk=self.driver.pk, results__race__season__pk=self.season.pk)
        self.teams = Team.objects.filter(seats__in=self.seats)
        self.teams_verbose = self.get_teams_verbose()

    def get_team_name_in_season(self, team):
        team_name = team.name
        team_season = TeamSeason.objects.filter(team=team, season=self.season)
        if team_season.exists():
            team_name = '{team}'.format(team=team_season.first().get_name_in_season())
        return team_name

    def get_teams_verbose(self):
        # In case of sponsor_name, it will be show in teams_verbose
        teams_verbose = []
        for team in self.teams:
            team_verbose = self.get_team_name_in_season(team=team)
            teams_verbose.append(team_verbose)
        return ', '.join(teams_verbose)

    def get_results(self, limit_races=None, **extra_filter):
        """ Return results. Can be limited."""
        extra_filter.update(**{'season': self.season})
        return Result.wizard(driver=self.driver, limit_races=limit_races, **extra_filter)

    def get_reverse_results(self, limit_races=None, **extra_filter):
        return self.get_results(limit_races=limit_races, reverse_order=True, **extra_filter)

    def get_stats(self, **filters):
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    def get_positions_in_row(self, limit_races=None, **extra_filter):
        results = self.get_results(limit_races=limit_races, **extra_filter)
        results = get_tuples_from_results(results)
        season_races = list(self.season.past_races.values_list('round', flat=True))
        positions_by_round = {result.round: result.finish for result in results}
        return [positions_by_round[x] for x in season_races if x in positions_by_round]

    def get_saved_points(self, limit_races=None):
        results = self.season.get_results_list()[self.driver]
        return [result.points for result in results if result.points]

    @property
    def is_active(self):
        return True

    def get_points_list(self, limit_races=None, punctuation_config=None, **kwargs):
        points_to_rank = kwargs.pop('points_to_rank', None)
        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races)
        else:
            points_list = []
            if points_to_rank:
                results = self.season.get_results_list()[self.driver]
            else:
                results = self.get_results(limit_races=limit_races, **kwargs)
            for result_tuple in get_tuples_from_results(results=results):
                points = PointsCalculator(punctuation_config).calculator(result_tuple)
                if points: points_list.append(points)
        return points_list

    def get_points(self, limit_races=None, punctuation_config=None, **kwargs):
        """ Get points. Can be limited. Punctuation config will be overwrite temporarily"""

        points_list = self.get_points_list(limit_races=limit_races, punctuation_config=punctuation_config, **kwargs)
        points_list = sorted(points_list, reverse=True)
        season_rounds = self.season.rounds
        if season_rounds:
            points_list = points_list[:season_rounds]
        return sum(points_list)

    def _summary_season(self, exclude_position=False):
        summary_season = {
            'season': self.season,
            'competition': self.season.competition,
            'year': self.season.year,
            'teams': self.teams_verbose
        }

        if not exclude_position:
            summary_season['pos'] = self.get_points_position()

        return summary_season



    def get_summary_stats(self, records_list=None, append_points=False, **kwargs):
        """
        Return multiple records (or only one) record in season

        """
        exclude_position = kwargs.pop('exclude_position', False)
        summary_stats = self._summary_season(exclude_position)
        summary_stats.update(
            stats=self.driver.get_stats_list(records_list=records_list, append_points=append_points,
                                                   season=self.season, **kwargs)
        )
        return summary_stats

    def get_points_position(self):

        """
        Return position in season rank

        """
        return self._points_position('points_rank', 'driver')


class RankModel(AbstractRankModel):
    @property
    def stats_filter_kwargs(self):
        return {}

    def get_stats_cls(self, driver):
        return driver

    def get_team_stats_cls(self, team):
        return team

    @property
    def drivers(self):
        return Driver.objects.all()

    @property
    def teams(self):
        return Team.objects.all()

    def __str__(self):
        return _('Global rank')

    class Meta:
        abstract = True
