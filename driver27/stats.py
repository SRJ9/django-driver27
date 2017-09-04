from .streak import Streak
from django.core.exceptions import ValidationError
from django.db import models
from .records import get_record_config
from . import LIMIT_POSITION_LIST


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

    def get_positions(self, qualifying=False, limit_races=None, competition=None, **kwargs):
        pos_field = 'qualifying' if qualifying else 'finish'
        results = self.get_results(limit_races=limit_races, competition=competition, **kwargs)
        positions = results.values_list(pos_field, flat=True)
        return list(positions)


    def get_positions_count_list(self, limit_races=None, competition=None, **kwargs):
        """ Return a list with the count of each 20 first positions """
        finish_pos = self.get_positions(limit_races=limit_races, competition=competition, **kwargs)
        positions_count = []
        for x in range(LIMIT_POSITION_LIST):
            position_count = finish_pos.count(x+1)
            positions_count.append(position_count)
        return positions_count

    def get_positions_count_str(self, position_list=None, limit_races=None):
        """ Return a str with position_count_list to order """
        " Each list item will be filled to zeros until get three digits e.g. 1 => 001, 12 => 012 "
        if not position_list:
            position_list = self.get_positions_count_list(limit_races=limit_races)
        positions_str = ''.join([str(x).zfill(3) for x in position_list])
        return positions_str


class AbstractStatsModel(models.Model):

    def get_results(self, *args, **kwargs):
        raise NotImplementedError('Not implemented property')

    @property
    def is_active(self):
        raise NotImplementedError('Not implemented property')


    def get_summary_points_rank(self, **kwargs):
        return self.get_summary_points(**kwargs)

    @property
    def result_filter_kwargs(self):
        raise NotImplementedError('Not implemented property')

    def season_stats_cls(self, *args, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_season(self, season):
        try:
            season_stats = self.season_stats_cls(season)
            return season_stats
        except ValidationError:
            return None

    def get_stats_list(self, records_list=None, append_points=False, **kwargs):
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


class TeamStatsModel(AbstractStatsModel, AbstractStreakModel):
    def season_stats_cls(self, *args, **kwargs):
        raise NotImplementedError('Not implemented method')


    @property
    def result_filter_kwargs(self):
        raise NotImplementedError('Not implemented property')

    @property
    def is_active(self):
        raise NotImplementedError('Not implemented property')

    def get_results(self, *args, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_total_races(self, **filters):
        """ Only count 1 by race with any driver in filter """
        return self.get_races(**filters).count()

    def get_total_stats(self, **filters):  # noqa
        """ Count 1 by each result """
        return self.get_results(**filters).count()

    def get_doubles_races(self, **filters):
        """ Only count 1 by race with at least two drivers in filter """
        return self.get_races(**filters).filter(count_race__gte=2).count()

    class Meta:
        abstract = True


class StatsByCompetitionModel(AbstractStatsModel, AbstractStreakModel):

    def get_points_by_season(self, season, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_summary_points(self, append_to_summary=None, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_stats_by_season(self, records_list=None, append_points=False, **kwargs):
        """
        Return multiple records (or only one) record in season

        """

        kwargs.pop('season', None)
        seasons = getattr(self, 'seasons').all()
        return [self.season_stats_cls(season=season) \
                    .get_summary_stats(records_list=records_list, append_points=append_points, **kwargs)
                for season in seasons]


    def get_stats_by_competition(self, records_list=None, append_points=False, **kwargs):
        competitions = getattr(self, 'competitions').all()
        return [
            {
                'competition': competition,
                'stats': self.get_stats_list(records_list=records_list,
                                             append_points=append_points,
                                             competition=competition, **kwargs)
            }
            for competition in competitions
        ]

    def seasons_by_competition(self, competition=None):
        seasons = getattr(self, 'seasons').all()
        if competition is not None:
            seasons = seasons.filter(competition=competition)
        return seasons

    def get_points(self, season=None, competition=None, punctuation_config=None):
        if season is not None:
            return self.get_season(season).get_points(punctuation_config=punctuation_config)
        seasons = self.seasons_by_competition(competition=competition)
        points = 0
        for season in seasons:
            season_points = self.get_season(season).get_points(punctuation_config=punctuation_config)
            points += season_points if season_points else 0
        return points

    class Meta:
        abstract = True

class SeasonStatsModel(object):

    def get_points_list(self, limit_races=None, punctuation_config=None, **kwargs):
        raise NotImplementedError('Not implemented method')

    def get_points(self, **kwargs):
        """ get_points in season must not be the same of other get_points because others is the sum of this """
        raise NotImplementedError('Not implemented method')

    def _summary_season(self, exclude_position=False):
        raise NotImplementedError('Not implemented method')

    def _points_position(self, rank, keyword):
        """
        Return position in season rank

        """
        attr = getattr(self, keyword)
        season = getattr(self, 'season')
        rank = getattr(season, rank)()
        position = None
        for index, entry in enumerate(rank):
            if attr == entry.get(keyword):
                position = index + 1
                break
        return position

    def get_summary_points_rank(self, **kwargs):
        return self.get_summary_points(points_to_rank=True, **kwargs)

    def get_summary_points(self, append_to_summary=None, **kwargs):
        exclude_position = kwargs.pop('exclude_position', False)
        punctuation_config = kwargs.pop('punctuation_config', None)
        summary_points = self._summary_season(exclude_position)
        if append_to_summary is None:
            append_to_summary = {}
        summary_points.update(
            points=self.get_points(punctuation_config=punctuation_config, **kwargs),
            pos_list=getattr(self, 'get_positions_count_list')(),
            pos_str=getattr(self, 'get_positions_count_str')(), **append_to_summary
        )


        return summary_points

    class Meta:
        abstract = True




