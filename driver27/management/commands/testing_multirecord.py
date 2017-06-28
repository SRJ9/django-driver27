from django.core.management.base import BaseCommand, CommandError
from driver27.models import Driver, Competition, Season
from driver27.records import get_record_config


class Command(BaseCommand):
    help = 'Test multirecord'

    def get_multirecord(self, driver, multirecords, **kwargs):
        multiple_records = {}
        for multirecord in multirecords:
            record_config = get_record_config(multirecord).get('filter')
            record_stat = driver.get_stats(**dict(kwargs, **record_config))
            multiple_records[multirecord] = record_stat
        return multiple_records

    def handle(self, *args, **options):
        driver = Driver.objects.get(pk=1)
        multirecords = ['PODIUM', 'POLE', 'WIN', 'FASTEST']

        competition = Competition.objects.get(pk=1)
        season_1 = Season.objects.get(pk=1)
        season_3 = Season.objects.get(pk=3)

        print(self.get_multirecord(driver, multirecords=multirecords, competition=competition))
        print(self.get_multirecord(driver, multirecords=multirecords, season=season_1))
        print(self.get_multirecord(driver, multirecords=multirecords, season=season_3))

