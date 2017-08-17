from django.core.management.base import BaseCommand, CommandError
from driver27.models import Season
import csv


class Command(BaseCommand):
    help = 'Create CSV for import result from last season'

    def add_arguments(self, parser):
        parser.add_argument('csv',)

    def handle(self, *args, **options):
        season = Season.objects.order_by('year', 'competition__name').last()
        season_seats = season.seats.all()
        season_pending_races = season.pending_races.order_by('round')

        with open(options['csv'], 'wb') as csvfile:
            fieldnames = ['driver', 'team', 'seat_id', 'race_id', 'race_round', 'qualifying', 'finish', 'retired',
                          'fastest_lap', 'wildcard']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for race in season_pending_races:
                for seat in season_seats:
                    writer.writerow(
                        {
                            'driver': str(seat.driver),
                            'team': str(seat.team),
                            'seat_id': seat.pk,
                            'race_id': race.pk,
                            'race_round': race.round,
                            'qualifying': None,
                            'finish': None,
                            'retired': '',
                            'fastest_lap': '',
                            'wildcard': ''
                        }
                    )
