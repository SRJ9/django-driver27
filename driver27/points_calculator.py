class PointsCalculator(object):
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

    def calculator(self, result):
        points = 0
        points += self.get_points_qualifying(result.qualifying)
        points += self.get_points_finish(result.finish, result.alter_punctuation)
        points += self.get_points_fastest_lap(result.fastest_lap)

        return points
