from .streak import Streak
from django.core.exceptions import ValidationError
from django.db import models
from .records import get_record_config


class AbstractStreakModel(object):
    def get_results(self, *args, **kwargs):
        raise NotImplementedError('Not implemented property')

    def get_reverse_results(self, *args, **kwargs):
        raise NotImplementedError('Not implemented property')

    @property
    def is_active(self):
        raise NotImplementedError('Not implemented property')

    def get_streak(self, max_streak=False, result_filter=None, unique_by_race=False, **filters):
        from .models import get_tuples_from_results
        if not result_filter:
            result_filter = {}
        results = self.get_reverse_results(**result_filter)
        results_tuples = get_tuples_from_results(results=results)
        return Streak(results=results_tuples, max_streak=max_streak, unique_by_race=unique_by_race).run(filters)

    def get_positions_list(self, limit_races=None, competition=None):
        """ Return a list with the count of each 20 first positions """
        results = self.get_results(limit_races=limit_races, competition=competition)
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


class AbstractStatsModel(AbstractStreakModel, models.Model):

    def get_results(self, *args, **kwargs):
        raise NotImplementedError('Not implemented property')

    @property
    def is_active(self):
        raise NotImplementedError('Not implemented property')

    @property
    def result_filter_kwargs(self):
        raise NotImplementedError('Not implemented property')

    def get_points(self, *args, **kwargs):
        raise NotImplementedError('Not implemented property')

    def season_stats_cls(self, *args, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_season(self, season):
        try:
            season_stats = self.season_stats_cls(season)
            return season_stats
        except ValidationError:
            return None

    def get_multiple_records(self, records_list=None, append_points=False, **kwargs):
        multiple_records = {}
        if records_list is None:
            records_list = ['RACE', 'POLE', 'WIN', 'PODIUM', 'FASTEST']
        for record in records_list:
            record_config = get_record_config(record).get('filter')
            if hasattr(self, 'get_total_races') and record == 'RACE':
                record_stat = self.get_total_races(**dict(kwargs, **record_config))
            else:
                record_stat = self.get_stats(**dict(kwargs, **record_config))
            multiple_records[record] = record_stat
        if append_points:
            multiple_records['POINTS'] = self.get_points(**kwargs)
        return multiple_records

    def get_saved_points(self, limit_races=None, **kwargs):
        results = self.get_results(limit_races=limit_races, **kwargs)
        return [result.points for result in results if not result.wildcard and result.points is not None]

    def get_reverse_results(self, limit_races=None, **extra_filter):
        return self.get_results(limit_races=limit_races, reverse_order=True, **extra_filter)

    def get_races(self, **filters):
        """ Return only race id of team in season """
        results = self.get_results(**filters).values('race').annotate(count_race=models.Count('race')).order_by()
        return results

    def get_stats(self, **filters):
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    class Meta:
        abstract = True


class TeamStatsModel(AbstractStatsModel):
    def get_total_races(self, **filters):
        """ Only count 1 by race with any driver in filter """
        return self.get_races(**filters).count()

    def get_doubles_races(self, **filters):
        """ Only count 1 by race with at least two drivers in filter """
        return self.get_races(**filters).filter(count_race__gte=2).count()

    def get_total_stats(self, **filters):  # noqa
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    def get_team_total_races(self, **filters):
        """ Only count 1 by race with any driver in filter """
        return self.get_races(**filters).count()

    def get_team_doubles_races(self, **filters):
        """ Only count 1 by race with at least two drivers in filter """
        return self.get_races(**filters).filter(count_race__gte=2).count()

    def get_team_total_stats(self, **filters):  # noqa
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    class Meta:
        abstract = True


class StatsByCompetitionModel(AbstractStatsModel):
    def get_multiple_records_by_competition(self, records_list=None, append_points=False, **kwargs):
        stats_by_competition = []
        for competition in getattr(self, 'competitions').all():
            stats_by_competition.append(
                {
                    'competition': competition,
                    'stats': self.get_multiple_records(records_list=records_list,
                                                       append_points=append_points,
                                                       competition=competition, **kwargs)
                }
            )
        return stats_by_competition

    class Meta:
        abstract = True





