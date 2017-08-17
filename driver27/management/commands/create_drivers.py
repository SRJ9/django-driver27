from django.core.management.base import BaseCommand, CommandError
from driver27.models import Driver
import csv


class Command(BaseCommand):
    help = 'Create drivers from CSV'

    @staticmethod
    def _create_driver(row):
        invalid_keywords = []

        driver_fields = [f.name for f in Driver._meta.get_fields()]
        for x in row:
            if x not in driver_fields:
                invalid_keywords.append(x)

        for invalid_keyword in invalid_keywords:
            del row[invalid_keyword]
        return Driver.objects.create(**row)

    def add_arguments(self, parser):
        parser.add_argument('csv',)

    def handle(self, *args, **options):
        with open(options['csv'], 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                self._create_driver(row)
