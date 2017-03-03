from driver27.models import Result, Season, Contender
from driver27.punctuation import get_punctuation_config
from collections import namedtuple

ResultTuple = namedtuple('ResultTuple', 'qualifying finish fastest_lap wildcard alter_punctuation')


class Scoring(object):
    def __init__(self, punctuation_config):
        self.punctuation_config = punctuation_config

    def get_points_qualifying(self, qualifying):
        qualifying_scoring = self.punctuation_config.get('qualifying')
        if qualifying_scoring and qualifying:
            scoring_len = len(qualifying_scoring)
            if not qualifying > scoring_len:
                return qualifying_scoring[qualifying - 1]
        return 0

    def get_points_finish(self, finish, alter_punctuation):
        points_factor = {'double': 2, 'half': 0.5}
        factor = points_factor[alter_punctuation] if alter_punctuation in points_factor else 1
        finish_scoring = self.punctuation_config.get('finish')
        if finish_scoring and finish:
            scoring_len = len(finish_scoring)
            if not finish > scoring_len:
                return finish_scoring[finish - 1] * factor
        return 0

    def get_points_fastest_lap(self, fastest_lap):
        if 'fastest_lap' in self.punctuation_config and fastest_lap:
            return self.punctuation_config.get('fastest_lap')
        else:
            return 0

    def point_calculator(self, result):
        points = 0
        if not result.wildcard:
            points += self.get_points_qualifying(result.qualifying)
            points += self.get_points_finish(result.finish, result.alter_punctuation)
            points += self.get_points_fastest_lap(result.fastest_lap)
        return points


def get_results(seat=None, contender=None, team=None, race=None, season=None, competition=None):
    filter_params = {}
    if seat:
        filter_params['seat'] = seat
    if contender:
        filter_params['seat__contender'] = contender
    if team:
        filter_params['seat__team'] = team
    if race:
        filter_params['race'] = race
    if season:
        filter_params['race__season'] = season
    if competition:
        filter_params['race__season__competition'] = competition

    results = Result.objects.filter(**filter_params) \
        .values_list('qualifying', 'finish', 'fastest_lap', 'wildcard', 'race__alter_punctuation')

    return results


def get_rank_points(punctuation=None):
    season = Season.objects.get(pk=1)
    contenders = season.contenders()

    if not punctuation:
        punctuation = season.punctuation

    punctuation_config = get_punctuation_config(punctuation)
    scoring = Scoring(punctuation_config)

    rank = []

    for contender in contenders:
        points_summary = []
        for result in get_results(contender=contender, season=season):
            print(result)
            result_tuple = ResultTuple(*result)
            points = scoring.point_calculator(result_tuple)
            if points:
                points_summary.append(points)
        rank.append({'contender': str(contender), 'points': sum(points_summary)})

    return rank