from django.core.management.base import BaseCommand, CommandError
from driver27.models import Result
import csv


class Command(BaseCommand):
    help = 'Update results via csv'

    @staticmethod
    def _create_result(row):
        for x in row:
            if x in ['qualifying', 'finish', 'points', 'race_id', 'seat_id']:
                if row[x] == '':
                    row[x] = None
                else:
                    row[x] = int(row[x])
            elif x in ['wildcard', 'fastest_lap', 'retired']:
                row[x] = bool(row[x])
        return Result.objects.create(**row)

    def add_arguments(self, parser):
        parser.add_argument('csv',)

    def handle(self, *args, **options):
        with open(options['csv'], 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                self._create_result(row)
