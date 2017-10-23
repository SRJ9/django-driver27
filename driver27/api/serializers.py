from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from ..models import GrandPrix, Circuit, Season, Competition, Driver, Team, Seat, Race, Result, SeatPeriod
from .common import DR27Serializer
from ..common import DRIVER27_API_NAMESPACE, DRIVER27_NAMESPACE

def get_view_name_detail(detail):
    return DRIVER27_NAMESPACE + ':' + DRIVER27_API_NAMESPACE + ':' + detail + '-detail'

class GrandPrixSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = GrandPrix
        fields = ('url', 'id', 'country', 'name', 'first_held', 'default_circuit', 'competitions',)
        extra_kwargs = {'url': {'view_name': get_view_name_detail('grandprix')}}


class CircuitSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Circuit
        fields = ('url', 'id', 'country', 'name', 'city', 'opened_in',)
        extra_kwargs = {'url': {'view_name': get_view_name_detail('circuit')}}


class SeasonSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    competition_details = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField(read_only=True)
    races = serializers.HyperlinkedRelatedField(view_name=get_view_name_detail('race'),
                                                many=True,
                                                read_only=True)

    def get_competition_details(self, obj):
        return CompetitionSerializer(instance=obj.competition, many=False,
                                     context=self.context, exclude_fields=['seasons', ]).data

    def get_slug(self, obj):
        return '-'.join((obj.competition.slug, str(obj.year)))

    class Meta:
        model = Season
        fields = ('url', 'id', 'year', 'rounds', 'slug', 'punctuation', 'competition',
                  'competition_details', 'races',)
        read_only_fields = ('competition_details', 'races',)
        extra_kwargs = {'url': {'view_name': get_view_name_detail('season')}}


class CompetitionSerializer(DR27Serializer, serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()
    seasons = SeasonSerializer(many=True, exclude_fields=['competition', 'competition_details', 'races'],
                               read_only=True)

    class Meta:
        model = Competition
        fields = ('url', 'id', 'name', 'full_name', 'country', 'slug', 'seasons')
        extra_kwargs = {'url': {'view_name': get_view_name_detail('competition')}}


class DriverSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Driver
        fields = ('url', 'id', 'last_name', 'first_name', 'year_of_birth', 'country', 'seats')
        read_only_fields = ('seats',)
        extra_kwargs = {'url': {'view_name': get_view_name_detail('driver')},
                        'seats': {'view_name': get_view_name_detail('seat')}
                        }


class NestedDriverSerializer(DriverSerializer):
    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country')


class TeamSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'id', 'name', 'full_name', 'competitions', 'country')
        extra_kwargs = {'url': {'view_name': get_view_name_detail('team')}}


class NestedTeamSerializer(TeamSerializer):
    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'country')


class SeatPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatPeriod
        fields = '__all__'


class SeatSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    team_details = serializers.SerializerMethodField()
    driver_details = serializers.SerializerMethodField()
    periods = serializers.SerializerMethodField()

    def get_team_details(self, obj):
        return TeamSerializer(instance=obj.team, many=False,
                              context=self.context).data

    def get_driver_details(self, obj):
        return DriverSerializer(instance=obj.driver, many=False, context=self.context).data

    def get_periods(self, obj):
        return SeatPeriodSerializer(instance=obj.periods, many=True, context=self.context).data

    class Meta:
        model = Seat
        fields = ('url', 'id', 'team', 'team_details', 'driver', 'driver_details', 'periods')
        read_only_fields = ('periods',)
        extra_kwargs = {'url': {'view_name': get_view_name_detail('seat')}}


class SeatRecapSerializer(serializers.ModelSerializer):
    driver_details = serializers.SerializerMethodField(method_name='get_driver')
    team = serializers.SerializerMethodField()

    def get_driver(self, obj):
        driver = obj.driver
        return {
            'id': driver.id,
            'first_name': driver.first_name,
            'last_name': driver.last_name
        }

    def get_team(self, obj):
        team = obj.team
        return {
            'id': team.id,
            'name': team.name
        }

    class Meta:
        model = Seat
        fields = ('driver_details', 'team')


class ResultSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    seat_details = serializers.SerializerMethodField()
    fastest_lap = serializers.SerializerMethodField()

    def get_fastest_lap(self, obj):
        return obj.is_fastest

    def get_seat_details(self, obj):
        return SeatRecapSerializer(instance=obj.seat,
                                   many=False,
                                   context=self.context).data

    class Meta:
        model = Result
        fields = ('url',
                  'id',
                  'race',
                  'seat',
                  'seat_details',
                  'qualifying',
                  'finish',
                  'fastest_lap',
                  'wildcard',
                  'retired',
                  'comment')
        extra_kwargs = {'url': {'view_name': get_view_name_detail('result')}}


class RaceSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    grand_prix_details = serializers.SerializerMethodField()
    circuit_details = serializers.SerializerMethodField()

    def get_grand_prix_details(self, obj):
        return GrandPrixSerializer(instance=obj.grand_prix,
                                   many=False,
                                   context=self.context,
                                   exclude_fields=['competitions', ]).data

    def get_circuit_details(self, obj):
        return CircuitSerializer(instance=obj.circuit,
                                 many=False,
                                 context=self.context).data

    class Meta:
        model = Race
        fields = ('url', 'id', 'season', 'round', 'grand_prix', 'grand_prix_details',
                  'circuit', 'circuit_details', 'date', 'alter_punctuation')

        extra_kwargs = {'url': {'view_name': get_view_name_detail('race')}}
