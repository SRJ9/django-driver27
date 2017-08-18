from django.core.management.base import BaseCommand, CommandError
from driver27.models import Driver, Team, Seat
import csv

class ImportOptionException(Exception):
    pass

class Command(BaseCommand):
    help = 'Import driver/team/seat from CSV'

    @staticmethod
    def create_entry(row, import_opt):
        invalid_keywords = []

        import_opts = {
            'drivers': Driver,
            'teams': Team,
            'seats': Seat
        }

        model_cls = import_opts.get(import_opt)
        if model_cls is None:
            raise ImportOptionException('Import param is invalid')

        model_fields = [f.column for f in model_cls._meta.get_fields() if hasattr(f, 'column')]

        for x in row:
            if x not in model_fields:
                invalid_keywords.append(x)

        for invalid_keyword in invalid_keywords:
            del row[invalid_keyword]
        if not row:
            return False
        return model_cls.objects.create(**row)

    def add_arguments(self, parser):
        parser.add_argument('csv',)
        parser.add_argument('import')

    def handle(self, *args, **options):
        with open(options['csv'], 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                self.create_entry(row, options['import'])
