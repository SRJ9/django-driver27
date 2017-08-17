# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from driver27.models import Driver, Team, Seat

import sys
if sys.version_info < (3, 0):
    try:
        import unicodecsv as csv
    except ImportError:
        import csv
else:
    import csv


class Command(BaseCommand):
    help = 'Export seats to csv'

    def get_config(self, export_attr):
        if export_attr == 'drivers':
            fieldnames = ['id', 'first_name', 'last_name', 'country', 'year_of_birth']
            export_cls = Driver
        elif export_attr == 'teams':
            fieldnames = ['id', 'name', 'full_name', 'country']
            export_cls = Team
        else:
            fieldnames = ['id', 'driver_id', 'driver__last_name', 'driver__first_name', 'team_id', 'team__name']
            export_cls = Seat
        objects = list(export_cls.objects.values(*fieldnames))
        return {'fieldnames': fieldnames, 'objects': objects}

    def add_arguments(self, parser):
        parser.add_argument('csv',)
        parser.add_argument(
            '--export',
            default='seats',
            help='By default, export seats. Options: seats, drivers, teams',
        )

    def handle(self, *args, **options):

        with open(options['csv'], 'wb') as csvfile:
            export_config = self.get_config(options['export'])
            writer = csv.DictWriter(csvfile, fieldnames=export_config['fieldnames'])
            writer.writeheader()

            for entry in export_config['objects']:
                writer.writerow(entry)
