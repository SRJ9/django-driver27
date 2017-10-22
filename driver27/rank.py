# encoding: utf-8
from .punctuation import get_punctuation_config
from django.db import models
from django.core.cache import cache
from six import text_type

try:
    from .models import Race
except ImportError:
    pass

try:
    from .models import Team
except ImportError:
    pass

from django.db.models import F, Sum
from .records import get_record_config


def order_points(rank):
    return sorted(rank, key=lambda x: (x['points'], x['pos_str']), reverse=True)


import re


class AbstractRankModel(models.Model):
    def get_stats_cls(self, contender):
        raise NotImplementedError('Not implemented method')

    def get_team_stats_cls(self, team):
        raise NotImplementedError('Not implemented method')


    @property
    def stats_filter_kwargs(self):
        raise NotImplementedError('Not implemented property')

    def get_name_cache_rank(self, prefix, kwargs):
        repr_kw = [u'{key}:{value}'.format(key=kw, value=kwargs.get(kw)) for kw in kwargs]
        repr_local = re.sub(r'[^\w:]', '', text_type(','.join(repr_kw)))
        cache_str = u'{prefix}_{repr_local}'.format(prefix=prefix, repr_local=repr_local)
        return cache_str

    def _abstract_points_rank_by_season(self, element_name, element_group, punctuation_config=None):
        rank = []
        items = getattr(self, element_group).all()
        for item in items:
            points_by_seasons = item.get_points_by_seasons(append_to_summary={element_name: item},
                                                             punctuation_config=punctuation_config,
                                                             **self.stats_filter_kwargs)
            for points_by_season in points_by_seasons:
                rank.append(points_by_season)
        return rank

    def _abstract_points_rank(self, element_name, element_group, stats_cls, punctuation_config=None):
        rank = []
        items= getattr(self, element_group).all()
        for item in items:
            stat_cls = stats_cls(item)
            rank.append(stat_cls.get_summary_points_rank(punctuation_config=punctuation_config,
                                                    exclude_position=True,
                                                    append_to_summary={element_name: item},
                                                    **self.stats_filter_kwargs))
        return rank

    def points_rank_by_season(self, punctuation_config=None):
        return self._abstract_points_rank_by_season('driver', 'drivers', punctuation_config)

    def team_points_rank_by_season(self, punctuation_config=None):
        return self._abstract_points_rank_by_season('team', 'teams', punctuation_config)

    def _points_rank(self, punctuation_config=None):
        return self._abstract_points_rank('driver', 'drivers', self.get_stats_cls, punctuation_config)

    def _team_points_rank(self, punctuation_config=None):
        return self._abstract_points_rank('team', 'teams', self.get_team_stats_cls, punctuation_config)

    def points_rank(self, punctuation_code=None, by_season=False):
        """ Points driver rank. Scoring can be override by scoring_code param """
        cache_str = self.get_name_cache_rank('points', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            punctuation_config = get_punctuation_config(punctuation_code=punctuation_code) \
                if punctuation_code is not None else None
            if by_season:
                rank = self.points_rank_by_season(punctuation_config=punctuation_config)
            else:
                rank = self._points_rank(punctuation_config=punctuation_config)
            cache.set(cache_str, rank)
        rank = order_points(rank)
        return rank

    def team_points_rank(self, punctuation_code=None, by_season=False):
        """ Same that points_rank by count both team drivers """
        cache_str = self.get_name_cache_rank('team_points', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            punctuation_config = get_punctuation_config(punctuation_code=punctuation_code) \
                if punctuation_code is not None else None
            teams = getattr(self, 'teams').all()
            if by_season:
                rank = self.team_points_rank_by_season(punctuation_config=punctuation_config)
            else:
                rank = self._team_points_rank(punctuation_config=punctuation_config)
            rank = order_points(rank)
            cache.set(cache_str, rank)
        return rank

    def olympic_rank(self):
        """ The driver
        with superior race results (based on descending order, from number of
        wins to numbers of second-places down) will gain precedence. """

        """ Points driver rank. Scoring can be override by scoring_code param """
        cache_str = self.get_name_cache_rank('olympic', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            drivers = getattr(self, 'drivers').all()
            rank = [self.get_stats_cls(driver).get_summary_points_rank(
                append_to_summary={'driver': driver},
                **self.stats_filter_kwargs) for driver in drivers]
        rank = sorted(rank, key=lambda x: x['pos_str'], reverse=True)
        cache.get(cache_str, rank)
        return rank

    def stats_rank(self, **filters):
        """ Get driver rank based on record filter """
        cache_str = self.get_name_cache_rank('stats', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            filters.update(**self.stats_filter_kwargs)
            drivers = getattr(self, 'drivers').all()
            rank = []
            for driver in drivers:
                stat_cls = self.get_stats_cls(driver)
                rank.append({'stat': stat_cls.get_stats(**filters),
                             'driver': driver,
                             'teams': stat_cls.teams_verbose})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    def comeback_rank(self):
        from .models import Result
        comeback_filter = get_record_config('COMEBACK').get('filter')
        comeback_filter.update(self.stats_filter_kwargs)
        cache_str = self.get_name_cache_rank('comeback', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            rank = Result.wizard(**comeback_filter) \
                .annotate(comeback=Sum(F('qualifying') - F('finish'))).order_by('-comeback')
            cache.set(cache_str, rank)
        return rank

    def seasons_rank(self, **filters):
        """ Get driver rank based on record filter """
        filters.update(**self.stats_filter_kwargs)
        cache_str = self.get_name_cache_rank('seasons', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            drivers = getattr(self, 'drivers').all()
            rank = []
            for driver in drivers:
                stat_cls = self.get_stats_cls(driver)
                driver_seasons = driver.seasons.filter(**self.stats_filter_kwargs)
                for season in driver_seasons:
                    rank.append({'stat': stat_cls.get_stats(season=season, **filters),
                                 'driver': driver,
                                 'teams': stat_cls.teams_verbose,
                                 'season': season})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    def seasons_team_rank(self, **filters):
        """ Get driver rank based on record filter """
        filters.update(**self.stats_filter_kwargs)
        cache_str = self.get_name_cache_rank('seasons_team', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            teams = getattr(self, 'teams').all()
            rank = []
            for team in teams:
                stat_cls = self.get_stats_cls(team)
                team_seasons = team.seasons.filter(**self.stats_filter_kwargs)
                for season in team_seasons:
                    rank.append({'stat': stat_cls.get_stats(season=season, **filters),
                                 'team': team,
                                 'season': season})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    def streak_rank(self, only_actives=False, max_streak=False, **filters):
        """ Get driver rank based on record filter """
        cache_str = self.get_name_cache_rank('streak', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            drivers = getattr(self, 'drivers').all()
            rank = []
            for driver in drivers:
                stat_cls = self.get_stats_cls(driver)
                if only_actives and not stat_cls.is_active:
                    continue
                rank.append({'stat': stat_cls.get_streak(result_filter=self.stats_filter_kwargs,
                                                         max_streak=max_streak, **filters),
                             'driver': driver,
                             'teams': stat_cls.teams_verbose})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    def streak_team_rank(self, only_actives=False, max_streak=False, **filters):
        """ Get team rank based on record filter """
        cache_str = self.get_name_cache_rank('streak_team', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            teams = getattr(self, 'teams').all()
            rank = []
            for team in teams:
                stat_cls = self.get_stats_cls(team)
                # if only_actives and not stat_cls.is_active:
                #     continue

                rank.append({'stat': stat_cls.get_streak(unique_by_race=True, result_filter=self.stats_filter_kwargs,
                                                         max_streak=max_streak, **filters),
                             'team': team})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    @staticmethod
    def get_team_rank_method(rank_type):
        """ Dict with distinct teams rank method, depending of rank_type param """
        " STATS: Count 1 by each time that driver get record "
        " RACES: Count 1 by each race that any driver get record "
        " DOUBLES: Count 1 by each race that at least two drivers get record "
        rank_dict = {
            'STATS': 'team_stats_rank',
            'RACES': 'team_races_rank',
            'DOUBLES': 'team_doubles_rank'
        }

        return rank_dict.get(rank_type)

    def get_team_rank(self, rank_type, **filters):
        """ Return team rank calling returned method by get_team_rank_method """
        rank_method = self.get_team_rank_method(rank_type)
        return getattr(self, rank_method)(**filters) if rank_method else None

        # if isinstance(self, Season):
        #     return TeamSeason.objects.get(season=self, team=team)
        # elif isinstance(self, Competition):
        #     return team

    def team_rank(self, total_method, **filters):
        """ Collect the records of each team calling the method of Team passed by total_method param """
        cache_str = self.get_name_cache_rank('team', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            rank = []
            teams = getattr(self, 'teams').all()
            for team in teams:
                team_stats_cls = self.get_team_stats_cls(team)
                total = getattr(team_stats_cls, total_method)(**filters)
                rank.append({'stat': total, 'team': team})
            rank = sorted(rank, key=lambda x: x['stat'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    def team_stats_rank(self, **filters):
        return self.team_rank('get_total_stats', **filters)

    def team_races_rank(self, **filters):
        return self.team_rank('get_total_races', **filters)

    def team_doubles_rank(self, **filters):
        return self.team_rank('get_doubles_races', **filters)

    def team_olympic_rank(self):
        """ Points team rank. Scoring can be override by scoring_code param """
        cache_str = self.get_name_cache_rank('olympic_team', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            teams = getattr(self, 'teams').all()
            rank = []
            for team in teams:
                stat_cls = self.get_stats_cls(team)
                position_count_list = stat_cls.get_positions_count_list(**self.stats_filter_kwargs)
                position_count_str = stat_cls.get_positions_count_str(position_list=position_count_list)
                rank.append({'pos_str': position_count_str,
                             'team': team,
                             'pos_list': position_count_list
                             })
            rank = sorted(rank, key=lambda x: x['pos_str'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    class Meta:
        abstract = True
