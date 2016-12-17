# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, IntegrityError
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, pre_save, pre_delete
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from . import punctuation
from slugify import slugify
from django_countries.fields import CountryField
from exclusivebooleanfield.fields import ExclusiveBooleanField


@python_2_unicode_compatible
class Driver(models.Model):
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
class Competition(models.Model):
    name = models.CharField(max_length=30, verbose_name=_('competition'), unique=True)
    full_name = models.CharField(max_length=100, unique=True, verbose_name=_('full name'))
    country = CountryField(null=True, blank=True, default=None, verbose_name=_('country'))
    slug = models.SlugField(null=True, blank=True, default=None)

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
class Contender(models.Model):
    driver = models.ForeignKey(Driver, related_name='career', verbose_name=_('driver'))
    competition = models.ForeignKey('Competition', related_name='contenders', verbose_name=_('competition'))
    teams = models.ManyToManyField('Team', through='Seat', related_name='contenders',
                                   verbose_name=_('teams'))

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
        return _('%(driver)s in %(competition)s') % {'driver': self.driver, 'competition': self.competition}

    class Meta:
        unique_together = ('driver', 'competition')
        ordering = ['competition__name', 'driver__last_name', 'driver__first_name']
        verbose_name = _('Contender')
        verbose_name_plural = _('Contenders')


@python_2_unicode_compatible
class Team(models.Model):
    name = models.CharField(max_length=75, verbose_name=_('team'), unique=True)
    full_name = models.CharField(max_length=200, unique=True, verbose_name=_('full name'))
    competitions = models.ManyToManyField('Competition', related_name='teams', verbose_name=_('competitions'))
    country = CountryField(verbose_name=_('country'))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')


@python_2_unicode_compatible
class Seat(models.Model):
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
class Season(models.Model):
    year = models.IntegerField(verbose_name=_('year'))
    competition = models.ForeignKey(Competition, related_name='seasons', verbose_name=_('competition'))
    rounds = models.IntegerField(blank=True, null=True, default=None, verbose_name=_('rounds'))
    teams = models.ManyToManyField(Team, related_name='seasons', through='TeamSeason',
                                   verbose_name=_('teams'))
    punctuation = models.CharField(max_length=20, null=True, default=None, verbose_name=_('punctuation'))

    def get_scoring(self, code=None):
        if not code:
            code = self.punctuation
        for scoring in punctuation.DRIVER27_PUNCTUATION:
            if scoring['code'] == code:
                return scoring
        return None

    def pending_races(self):
        past_races = Race.objects.filter(season=self, results__pk__isnull=False).distinct().count()
        pending_races = (self.rounds - past_races)
        return pending_races

    def pending_points(self):
        scoring = self.get_scoring()
        max_score_by_race = sorted(scoring['finish'], reverse=True)[0]
        pending_races = self.pending_races()
        return pending_races * max_score_by_race

    def has_champion(self):
        leader_points = self.leader[0] if self.leader else 0
        runner_up_points = self.runner_up[0] if self.runner_up else 0
        pending_points = self.pending_points()
        leader_distance = leader_points - runner_up_points
        return leader_distance >= pending_points

    def contenders(self):
        seats = [seat.pk for seat in self.seats.all()]
        return Contender.objects.filter(seats__pk__in=seats).distinct()

    def stats_rank(self, **filters):
        contenders = self.contenders()
        rank = []
        for contender in contenders:
            contender_season = contender.get_season(self)
            rank.append((contender_season.get_stats(**filters), contender.driver, contender_season.teams_verbose))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def team_stats_rank(self, unique_by_race=False, **filters):
        teams = self.teams.all()
        rank = []
        for team in teams:
            team_season = TeamSeason.objects.get(season=self, team=team)
            rank.append((team_season.get_stats(unique_by_race=unique_by_race, **filters), team))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def points_rank(self, scoring_code=None):
        contenders = self.contenders()
        scoring = self.get_scoring(scoring_code)
        rank = []
        for contender in contenders:
            contender_season = contender.get_season(self)
            rank.append((contender_season.get_points(scoring=scoring), contender.driver, contender_season.teams_verbose, contender_season.get_positions_str()))
        rank = sorted(rank, key=lambda x: (x[0], x[3]), reverse=True)
        return rank

    def olympic_rank(self):
        contenders = self.contenders()
        rank = []
        for contender in contenders:
            contender_season = contender.get_season(self)
            position_list = contender_season.get_positions_list()
            position_str = contender_season.get_positions_str(position_list=position_list)
            rank.append((position_str,
                         contender.driver,
                         contender_season.teams_verbose,
                         position_list))
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
    def runner_up(self):
        rank = self.points_rank()
        return rank[1] if len(rank) > 1 else None

    @property
    def team_leader(self):
        return self.get_leader(team=True)

    def __str__(self):
        return '/'.join((self.competition.name, str(self.year)))

    class Meta:
        unique_together = ('year', 'competition')
        ordering = ['competition__name', 'year']
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')


class SeatsSeason(Season):
    # aux proxy class to use in Admin for Season/Seat relation from Season
    class Meta:
        proxy = True
        verbose_name = _('Seats by season')
        verbose_name_plural = _('Seats by season')


@python_2_unicode_compatible
class Race(models.Model):
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
                errors['round'] = _('Max rounds in this season: %(rounds)d') % {'rounds': self.season.rounds}
            if self._grandprix_exception():
                errors['grand_prix'] = _("%(grand_prix)s is not a/an %(competition)s Grand Prix") \
                                       % {'grand_prix': self.grand_prix, 'competition': self.season.competition}
        if errors:
            raise ValidationError(errors)
        super(Race, self).clean()

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
        verbose_name = _('Race')
        verbose_name_plural = _('Races')


class SeatSeason(models.Model):
    seat = models.ForeignKey('Seat', related_name='seasons_seat')
    season = models.ForeignKey('Season', related_name='seats_season')

    @staticmethod
    def get_seat_season_errors(seat, season):
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
        errors = []
        if season.pk:
            season_teams = [season_team.pk for season_team in season.teams.all()]
            if team.pk not in season_teams:
                errors.append(
                    _('%(team)s is not a team of %(season)s') % {'team': team, 'season': season}
                )
        return errors

    def clean(self, *args, **kwargs):
        seat = self.seat
        season = self.season
        errors = []
        errors.extend(self.get_seat_season_errors(seat, season))
        errors.extend(self.get_seat_team_season_error(seat.team, season))
        if errors:
            raise ValidationError(errors)
        super(SeatSeason, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        super(SeatSeason, self).save(*args, **kwargs)

    class Meta:
        auto_created = True
        db_table = 'driver27_seat_seasons'


def seat_seasons(sender, instance, action, pk_set, **kwargs):  #noqa
    # """ Signal in DriverCompetitionTeam.seasons to avoid seasons which not is in competition"""
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
class TeamSeason(models.Model):
    season = models.ForeignKey('Season', related_name='teams_season', verbose_name=_('season'))
    team = models.ForeignKey('Team', related_name='seasons_team', verbose_name=_('team'))
    sponsor_name = models.CharField(max_length=75, null=True, blank=True, default=None,
                                    verbose_name=_('sponsor name'))

    def clean(self, *args, **kwargs):
        if hasattr(self, 'team') and hasattr(self, 'season'):
            team = self.team
            team_competitions = [competition.pk for competition in team.competitions.all()]
            if self.season.competition.pk not in team_competitions:
                raise ValidationError(
                    _('Team %(team)s doesn\'t participate in %(competition)s')
                    % {'team': self.team, 'competition': self.season.competition}
                )
        super(TeamSeason, self).clean()

    @staticmethod
    def delete_seat_exception(team, season):
        if TeamSeason.check_delete_seat_restriction(team=team, season=season):
            raise IntegrityError('You cannot delete a team with seats in this season.'
                                  'Delete seats before')


    @staticmethod
    def check_delete_seat_restriction(team, season):
        seats_count = SeatSeason.objects.filter(seat__team=team, season=season).count()
        return bool(seats_count)
        # return {'team': _('Seats with %(team)s exists in this season. Delete seats before.' % {'team': team})}

    def get_results(self, limit_races=None):
        results = Result.objects.filter(race__season=self.season, seat__team=self.team)
        if isinstance(limit_races, int):
            results = results.filter(race__round__lte=limit_races)
        results = results.order_by('race__round')
        return results

    def get_races(self, **filters):
        results = self.get_results().filter(**filters)\
            .values('race').annotate(count_race=models.Count('race'))\
            .order_by()
        return results

    def get_points(self):
        results = self.get_results().exclude(wildcard=True).order_by('race__round')
        points_list = [result.points for result in results.all() if result.points is not None]
        return sum(points_list)

    def get_filtered_results(self, **filters):
        results = self.get_results()
        return results.filter(**filters)

    def get_filtered_races(self, **filters):
        return self.get_races(**filters)

    def get_stats(self, unique_by_race=False, **filters):
        if unique_by_race:
            return self.get_filtered_races(**filters).count()
        return self.get_filtered_results(**filters).count()

    # def delete(self, *args, **kwargs):
    #     team = self.team
    #     season = self.season
    #     self.delete_seat_exception(team=team, season=season)
    #     super(TeamSeason, self).delete(*args, **kwargs)

    def __str__(self):
        str_team = self.team.name
        if self.sponsor_name:
            str_team = self.sponsor_name
        return '%s in %s' % (str_team, self.season)

    class Meta:
        unique_together = ('season', 'team')
        verbose_name = _('Team Season')
        verbose_name_plural = _('Teams Season')


@python_2_unicode_compatible
class Result(models.Model):
    race = models.ForeignKey(Race, related_name='results', verbose_name=_('race'))
    seat = models.ForeignKey(Seat, related_name='results', verbose_name=_('seat'))
    qualifying = models.IntegerField(blank=True, null=True, default=None, verbose_name=_('qualifying'))
    finish = models.IntegerField(blank=True, null=True, default=None, verbose_name=_('finish'))
    fastest_lap = ExclusiveBooleanField(on='race', default=False, verbose_name=_('fastest lap'))
    retired = models.BooleanField(default=False, verbose_name=_('retired'))
    wildcard = models.BooleanField(default=False, verbose_name=_('wildcard'))
    comment = models.CharField(max_length=250, blank=True, null=True, default=None, verbose_name=_('comment'))

    def clean(self, *args, **kwargs):
        seat_errors = []
        if self.seat.team not in self.race.season.teams.all():
            seat_errors.append(_('Team is not in current season'))
        if self.seat not in self.race.season.seats.all():
            seat_errors.append(_('Seat is not in current season'))
        if seat_errors:
            raise ValidationError(_('Invalid Seat in this race. ')+'\n'.join(seat_errors))
        super(Result, self).clean()

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

    def points_calculator(self, scoring):
        points = 0
        if not scoring:
            scoring = self.race.season.get_scoring()
        points += self._get_fastest_lap_points(scoring)
        points += self._get_race_points(scoring)
        return points if points > 0 else None

    @property
    def points(self):
        scoring = self.race.season.get_scoring()
        return self.points_calculator(scoring)

    def __str__(self):
        string = '%s (%s)' % (self.seat, self.race)
        if self.finish:
            string += ' - %sº' % self.finish
        else:
            string += ' - ' + _('OUT')
        return string

    class Meta:
        unique_together = [('race', 'seat'), ('race', 'qualifying'), ('race', 'finish')]
        ordering = ['race__season', 'race__round', 'finish', 'qualifying']
        verbose_name = _('Result')
        verbose_name_plural = _('Results')


class ContenderSeason(object):
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

    def get_results(self, limit_races=None):
        results = Result.objects.filter(race__season=self.season, seat__contender=self.contender)
        if isinstance(limit_races, int):
            results = results.filter(race__round__lte=limit_races)
        results = results.order_by('race__round')
        return results

    def get_filtered_results(self, **filters):
        results = self.get_results()
        return results.filter(**filters)

    def get_stats(self, **filters):
        return self.get_filtered_results(**filters).count()

    def get_points(self, limit_races=None, scoring=None):
        results = self.get_results(limit_races=limit_races)
        points_list = []
        for result in results.all():
            result_points = result.points_calculator(scoring)
            if result_points:
                points_list.append(result_points)
        return sum(points_list)
        
    def get_positions_list(self, limit_races=None):
        results = self.get_results(limit_races=limit_races)
        last_position=20
        positions = []
        for x in range(1, last_position+1):
            position_count = results.filter(finish=x).count()
            positions.append(position_count)
        return positions

    def get_positions_str(self, position_list=None, limit_races=None):
        if not position_list:
            position_list = self.get_positions_list(limit_races=limit_races)
        positions_str = ''.join([str(x).zfill(3) for x in position_list])
        return positions_str


@receiver(pre_save)
def pre_save_handler(sender, instance, *args, **kwargs):
    model_list = (Driver, Team, Competition, Contender, Seat, Circuit,
                  GrandPrix, Race, Season, Result, SeatSeason, TeamSeason)
    if not isinstance(instance, model_list):
        return
    instance.full_clean()


@receiver(pre_delete, sender=TeamSeason)
def pre_delete_team_season(sender, instance, *args, **kwargs):
    team = instance.team
    season = instance.season
    TeamSeason.delete_seat_exception(team=team, season=season)
