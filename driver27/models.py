# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from .points_calculator import PointsCalculator
from .punctuation import get_punctuation_config
from slugify import slugify
from django_countries.fields import CountryField
from exclusivebooleanfield.fields import ExclusiveBooleanField
from swapfield.fields import SwapIntegerField
from . import lr_intr, lr_diff
from .stats import AbstractStreakModel, AbstractStatsModel, TeamStatsModel, StatsByCompetitionModel
from .rank import AbstractRankModel

from django.db.models import Q
from collections import namedtuple

ResultTuple = namedtuple('ResultTuple', 'qualifying finish fastest_lap wildcard retired race_id alter_punctuation')


def get_tuples_from_results(results):
    return [get_tuple_from_result(result) for result in results]


def get_tuple_from_result(result):
    return ResultTuple(result.qualifying, result.finish, result.fastest_lap,
                       result.wildcard, result.retired, result.race_id, result.race.alter_punctuation)


def get_results_tuples(seat=None, team=None, race=None, season=None, competition=None,
                       results=None, skip_results_if_false=False, **extra_filters):

    # Result can be the only param passed to get_results_tuple.
    # If results=false, get_results will be calculate without params, return all results of all competitions.
    # If skip_results_if_false is True, results will be skipped but return ResultTuple structure.
    if not results and not skip_results_if_false:
        results = Result.wizard(seat=seat, team=team, race=race,
                                season=season, competition=competition, **extra_filters)

    results = results.values_list('qualifying', 'finish', 'fastest_lap', 'wildcard', 'retired',
                                  'race_id', 'race__alter_punctuation')

    return results


@python_2_unicode_compatible
class Driver(StatsByCompetitionModel):
    """ Main Driver Model. To combine with competitions (Contender) and competition/team (Seat) """
    last_name = models.CharField(max_length=50, verbose_name=_('last name'))
    first_name = models.CharField(max_length=25, verbose_name=_('first name'))
    year_of_birth = models.IntegerField(verbose_name=_('year of birth'), null=True, blank=True)
    country = CountryField(verbose_name=_('country'), null=True, blank=True)
    teams = models.ManyToManyField('Team', through='Seat', related_name='drivers', verbose_name=_('teams'))

    @property
    def result_filter_kwargs(self):
        return {}

    @property
    def seasons(self):
        return Season.objects.filter(races__results__seat__driver=self).distinct()

    @property
    def competitions(self):
        return Competition.objects.filter(seasons__in=self.seasons.all()).distinct()

    @property
    def is_active(self):
        seasons_ordered_by_desc_year = Season.objects.order_by('-year')
        if seasons_ordered_by_desc_year.count():
            last_year = seasons_ordered_by_desc_year[0].year
            return Result.objects.filter(seat__driver=self, race__season__year=last_year).count()
        else:
            return True

    def _teams_verbose(self, teams):
        return ', '.join([team.name for team in teams])

    @property
    def teams_verbose(self):
        return self._teams_verbose(self.teams.all())

    def get_results(self, limit_races=None, **extra_filter):
        return Result.wizard(driver=self, limit_races=limit_races, **extra_filter)

    def get_saved_points(self, limit_races=None, **kwargs):
        results = self.get_results(limit_races=limit_races, **kwargs)
        points = results.values_list('points', flat=True)
        return [point for point in points if point]

    def get_points(self, limit_races=None, punctuation_config=None, **kwargs):
        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races, **kwargs)
        else:
            points_list = []
            results = self.get_results(limit_races=limit_races, **kwargs)
            # Result can be the only param passed to get_results_tuple.
            # If results=false, get_results will be calculate without params, return all results of all competitions.
            # If skip_results_if_false is True, results will be skipped but return ResultTuple structure.
            for result in get_results_tuples(results=results, skip_results_if_false=True):
                result_tuple = ResultTuple(*result)
                points = PointsCalculator(punctuation_config).calculator(result_tuple, skip_wildcard=True)
                if points:
                    points_list.append(points)
        return sum(points_list)

    def season_stats_cls(self, season):
        return ContenderSeason(driver=self, season=season)

    def get_multiple_records_by_season(self, records_list=None, append_points=False, **kwargs):
        stats_by_season = []
        for season in self.seasons.all():
            stats_by_season.append(
                {
                    'competition': season.competition,
                    'year': season.year,
                    'teams': self.get_season(season=season).teams_verbose,
                    'stats': self.get_multiple_records(records_list=records_list,
                                                       append_points=append_points, season=season, **kwargs)
                }
            )
        return stats_by_season

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

    @property
    def drivers(self):
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
    competitions = models.ManyToManyField('Competition', through='CompetitionTeam', related_name='teams', verbose_name=_('competitions'))
    country = CountryField(verbose_name=_('country'), blank=True, null=True)

    @property
    def seasons(self):
        return Season.objects.filter(races__results__seat__team=self).distinct()

    def get_results(self, competition=None, **extra_filter):
        """ Return all results of team in season """
        return Result.wizard(team=self, competition=competition, **extra_filter)

    def season_stats_cls(self, season):
        return TeamSeason.objects.get(season=season, team=self)

    def get_total_races(self, competition=None, **filters):
        return super(Team, self).get_total_races(competition=competition, **filters)

    def get_doubles_races(self, competition=None, **filters):
        return super(Team, self).get_doubles_races(competition=competition, **filters)

    def get_total_stats(self, competition=None, **filters):
        return super(Team, self).get_total_stats(competition=competition, **filters)

    def get_points(self, season=None, competition=None, punctuation_config=None):
        if season is not None:
            return self.get_season(season).get_points(punctuation_config=punctuation_config)
        competition_filter = {}
        if competition is not None:
            competition_filter = {'competition': competition}
        seasons = Season.objects.filter(races__results__seat__team=self, **competition_filter).distinct()
        points = 0
        for season in seasons:
            season_points = self.get_season(season).get_points(punctuation_config=punctuation_config)
            points += season_points if season_points else 0
        return points

    def get_multiple_records_by_season(self, records_list=None, append_points=False, **kwargs):
        stats_by_season = []
        for season in self.seasons.all():
            num_of_seats = season.seats.filter(team=self)
            stats_by_season.append(
                {
                    'competition': season.competition,
                    'year': season.year,
                    'num_of_seats': num_of_seats,
                    'stats': self.get_multiple_records(records_list=records_list,
                                                       append_points=append_points, season=season, **kwargs)
                }
            )
        return stats_by_season



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

    @property
    def stats_filter_kwargs(self):
        return {}

    @property
    def drivers(self):
        """ As season is related with seats, this method is a shorcut to get drivers """
        return Driver.objects.filter(seats__results__race__season=self).distinct()

    @property
    def teams(self):
        """ As season is related with seats, this method is a shorcut to get teams """
        return Team.objects.filter(seats__results__race__season=self).distinct()

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

    def pending_races(self):
        """ Based on rounds field, return races count when race doesn't have any result """
        """ If rounds is None, rounds will setted to races in season"""
        races = Race.objects.filter(season=self)
        past_races = races.filter(results__pk__isnull=False).distinct().count()
        rounds = self.rounds
        if rounds is None:
            rounds = Race.objects.filter(season=self).count()
        pending_races = (rounds - past_races)
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
        return leader['points'] - pending_points if leader else None

    def only_title_contenders(self, punctuation_code=None):
        """ They are only candidates for the title if they can reach the leader by adding all the pending points."""
        rank = self.points_rank(punctuation_code=punctuation_code)
        leader_window = self.leader_window(rank=rank, punctuation_code=punctuation_code)

        title_rank = []
        if leader_window:
            title_rank = [entry for entry in rank if entry['points'] >= leader_window]
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
        return Result.wizard(limit_races=limit_races, **dict(results_filter, **extra_filter))

    def get_points(self, limit_races=None, punctuation_config=None, **kwargs):
        """ Get points. Can be limited. Punctuation config will be overwrite temporarily"""

        if punctuation_config is None:
            points_list = self.get_saved_points(limit_races=limit_races, **kwargs)
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

    def get_name_in_season(self):
        str_team = self.team.name
        if self.sponsor_name:
            str_team = self.sponsor_name
        return str_team

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
    qualifying = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None, verbose_name=_('qualifying'))
    finish = SwapIntegerField(unique_for_fields=['race'], blank=True, null=True, default=None, verbose_name=_('finish'))
    fastest_lap = ExclusiveBooleanField(on='race', default=False, verbose_name=_('fastest lap'))
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
                key = key_in_filters.get(kwarg) # the key of filter is the value of kwarg in key_in_filter
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
        if Result.objects.filter(seat__driver=self.seat.driver, race=self.race).exclude(pk=self.pk).exists():
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

    @property
    def driver(self):
        return self.seat.driver

    @property
    def team(self):
        return self.seat.team

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


class ContenderSeason(AbstractStreakModel):
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

    def get_teams_verbose(self):
        # In case of sponsor_name, it will be show in teams_verbose
        teams_verbose = []
        for team in self.teams:
            team_season = TeamSeason.objects.filter(team=team, season=self.season)
            if team_season.exists():
                team_verbose = '{team}'.format(team=team_season.first().get_name_in_season())
            else:
                team_verbose = team.name
            teams_verbose.append(team_verbose)
        return ', '.join(teams_verbose)

    def get_results(self, limit_races=None, **extra_filter):
        """ Return results. Can be limited."""
        return Result.wizard(driver=self.driver, season=self.season, limit_races=limit_races, **extra_filter)

    def get_reverse_results(self, limit_races=None, **extra_filter):
        return self.get_results(limit_races=limit_races, reverse_order=True, **extra_filter)

    def get_stats(self, **filters):
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    def get_saved_points(self, limit_races=None):
        results = self.get_results(limit_races=limit_races)
        points = results.values_list('points', flat=True)
        return [point for point in points if point]

    @property
    def is_active(self):
        return True

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
