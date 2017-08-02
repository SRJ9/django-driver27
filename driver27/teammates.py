from .models import Race, Team, Driver, Result


class Teammates(object):

    def group_results_by_race(self, results):
        group_by_race = {}
        for result in results:
            if result.race not in group_by_race:
                group_by_race[result.race] = []
            group_by_race[result.race].append(result)
        return group_by_race

    def group_results(self, results):
        results = results.order_by('race_id', 'seat__team')
        results_by_race = self.group_results_by_race(results)

    def wizard(self, race=None, team=None, driver=None):
        results = Result.wizard
        if race is not None:
            race_filter = {'race': race}
            results = results(**race_filter)
        if team is not None:
            team_filter = {'race': team.races.all()}
            results = results(**team_filter)
        if driver is not None:
            driver_filter = {'race': driver.races.all()}
            results = results(**driver_filter)
        self.group_results(results)

    class Meta:
        abstract = True
