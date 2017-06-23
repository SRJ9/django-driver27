from .punctuation import get_punctuation_config
from django.db import models
try:
    from .models import Race
except ImportError:
    pass

try:
    from .models import Team
except ImportError:
    pass




class AbstractRankModel(models.Model):

    def get_stats_cls(self, contender):
        raise NotImplementedError('Not implemented method')

    def get_team_stats_cls(self, team):
        raise NotImplementedError('Not implemented method')

    @property
    def stats_filter_kwargs(self):
        raise NotImplementedError('Not implemented property')

    def points_rank(self, punctuation_code=None):
        """ Points driver rank. Scoring can be override by scoring_code param """
        punctuation_config = None
        if punctuation_code:
            punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
        drivers = getattr(self, 'drivers').all()
        rank = []
        for driver in drivers:
            stat_cls = self.get_stats_cls(driver)
            rank.append((stat_cls.get_points(punctuation_config=punctuation_config, **self.stats_filter_kwargs), driver,
                         stat_cls.teams_verbose, stat_cls.get_positions_str()))
        rank = sorted(rank, key=lambda x: (x[0], x[3]), reverse=True)
        return rank

    def olympic_rank(self):
        """ The driver
        with superior race results (based on descending order, from number of
        wins to numbers of second-places down) will gain precedence. """

        """ Points driver rank. Scoring can be override by scoring_code param """
        drivers = getattr(self, 'drivers').all()
        rank = []
        for driver in drivers:
            stat_cls = self.get_stats_cls(driver)
            position_list = stat_cls.get_positions_list(**self.stats_filter_kwargs)
            position_str = stat_cls.get_positions_str(position_list=position_list)
            rank.append((position_str, driver,
                         stat_cls.teams_verbose, position_list))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def team_points_rank(self, punctuation_code=None):
        """ Same that points_rank by count both team drivers """
        punctuation_config = None
        if punctuation_code:
            punctuation_config = get_punctuation_config(punctuation_code=punctuation_code)
        teams = getattr(self, 'teams').all()
        rank = []
        for team in teams:
            team_stats_cls = self.get_team_stats_cls(team)
            team_stats_kw = self.stats_filter_kwargs
            rank.append((team_stats_cls.get_points(punctuation_config=punctuation_config, **team_stats_kw), team,
                         team_stats_cls.get_positions_str()))
        rank = sorted(rank, key=lambda x: (x[0], x[2]), reverse=True)
        return rank

    def stats_rank(self, **filters):
        """ Get driver rank based on record filter """
        filters.update(**self.stats_filter_kwargs)
        contenders = getattr(self, 'drivers').all()
        rank = []
        for contender in contenders:
            stat_cls = self.get_stats_cls(contender)
            rank.append((stat_cls.get_stats(**filters), contender, stat_cls.teams_verbose))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def streak_rank(self, only_actives=False, max_streak=False, **filters):
        """ Get driver rank based on record filter """
        contenders = getattr(self, 'drivers').all()
        rank = []
        for contender in contenders:
            stat_cls = self.get_stats_cls(contender)
            if only_actives and not stat_cls.is_active:
                continue
            rank.append((stat_cls.get_streak(result_filter=self.stats_filter_kwargs, max_streak=max_streak, **filters), contender, stat_cls.teams_verbose))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
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
        rank = []
        teams = getattr(self, 'teams').all()
        for team in teams:
            team_stats_cls = self.get_team_stats_cls(team)
            total = getattr(team_stats_cls, total_method)(**filters)
            rank.append((total, team))
        rank = sorted(rank, key=lambda x: x[0], reverse=True)
        return rank

    def team_stats_rank(self, **filters):
        return self.team_rank('get_total_stats', **filters)

    def team_races_rank(self, **filters):
        return self.team_rank('get_total_races', **filters)

    def team_doubles_rank(self, **filters):
        return self.team_rank('get_doubles_races', **filters)

    class Meta:
        abstract = True


