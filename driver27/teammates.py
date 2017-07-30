from .models import Race, Team, Driver, Result


class Teammates(object):
    def group_results(self, results):
        results = results.order_by('race_id', 'seat__team')

        groups = []
        for result in results:
            pass

    def wizard(self, race=None, team=None, driver=None):
        results = Result.objects
        if race is not None:
            race_filter = {'race': race}
            results = results.filter(**race_filter)
        if team is not None:
            team_filter = {'race': team.races.all()}
            results = results.filter(**team_filter)
        if driver is not None:
            driver_filter = {'race': driver.races.all()}
            results = results.filter(**driver_filter)
        self.group_results(results)






    class Meta:
        abstract = True
