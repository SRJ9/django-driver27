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

    def points_rank(self, punctuation_code=None, by_season=False):
        """ Points driver rank. Scoring can be override by scoring_code param """
        cache_str = self.get_name_cache_rank('points', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            punctuation_config = None
            if punctuation_code:
                punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
            drivers = getattr(self, 'drivers').all()
            rank = []
            if by_season:
                for driver in drivers:
                    seasons_by_driver = driver.get_points_by_seasons(append_driver=True,
                                                                     punctuation_config=punctuation_config,
                                                                     **self.stats_filter_kwargs)
                    for season_by_driver in seasons_by_driver:
                        rank.append(season_by_driver)
            else:
                for driver in drivers:
                    stat_cls = self.get_stats_cls(driver)
                    rank.append({'points': stat_cls.get_points(punctuation_config=punctuation_config,
                                                               **self.stats_filter_kwargs),
                                 'driver': driver,
                                 'teams': stat_cls.teams_verbose,
                                 'pos_str': stat_cls.get_positions_str()
                                 })
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
            rank = []
            for driver in drivers:
                stat_cls = self.get_stats_cls(driver)
                position_list = stat_cls.get_positions_list(**self.stats_filter_kwargs)
                position_str = stat_cls.get_positions_str(position_list=position_list)
                rank.append({'pos_str': position_str,
                             'driver': driver,
                             'teams': stat_cls.teams_verbose,
                             'pos_list': position_list
                             })
            rank = sorted(rank, key=lambda x: x['pos_str'], reverse=True)
            cache.get(cache_str, rank)
        return rank

    def team_points_rank(self, punctuation_code=None, by_season=False):
        """ Same that points_rank by count both team drivers """
        cache_str = self.get_name_cache_rank('team_points', locals())
        cache_rank = cache.get(cache_str)

        if cache_rank:
            rank = cache_rank
        else:
            punctuation_config = None
            if punctuation_code:
                punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
            teams = getattr(self, 'teams').all()
            rank = []
            if by_season:
                for team in teams:
                    seasons_by_team = team.get_points_by_seasons(append_team=True,
                                                                 punctuation_config=punctuation_config,
                                                                 **self.stats_filter_kwargs)
                    for season_by_team in seasons_by_team:
                        rank.append(season_by_team)
            else:
                for team in teams:
                    team_stats_cls = self.get_team_stats_cls(team)
                    team_stats_kw = self.stats_filter_kwargs
                    rank.append({'points': team_stats_cls.get_points(punctuation_config=punctuation_config,
                                                                     **team_stats_kw),
                                 'team': team,
                                 'pos_str': team_stats_cls.get_positions_str()
                                 })
            rank = order_points(rank)
            cache.set(cache_str, rank)
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
            rank = Result.wizard(**comeback_filter)\
                .annotate(comeback=Sum(F('qualifying')-F('finish'))).order_by('-comeback')
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
                if only_actives and not stat_cls.is_active:
                    continue

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

    def olympic_team_rank(self):
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
                position_list = stat_cls.get_positions_list(**self.stats_filter_kwargs)
                position_str = stat_cls.get_positions_str(position_list=position_list)
                rank.append({'pos_str': position_str,
                             'team': team,
                             'pos_list': position_list
                             })
            rank = sorted(rank, key=lambda x: x['pos_str'], reverse=True)
            cache.set(cache_str, rank)
        return rank

    class Meta:
        abstract = True


