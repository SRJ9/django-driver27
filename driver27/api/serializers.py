from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from ..models import GrandPrix, Circuit, Season, Competition, Driver, Team, Contender, Seat, Race, Result
from .common import DR27Serializer


class GrandPrixSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = GrandPrix
        fields = ('url', 'id', 'country', 'name', 'first_held', 'default_circuit', 'competitions',)


class CircuitSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Circuit
        fields = ('url', 'id', 'country', 'name', 'city', 'opened_in',)


class SeasonSerializer(DR27Serializer, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    competition_details = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField(read_only=True)
    races = serializers.HyperlinkedRelatedField(view_name='race-detail',
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


class CompetitionSerializer(DR27Serializer, serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()
    seasons = SeasonSerializer(many=True, exclude_fields=['competition', 'competition_details', 'races'])

    class Meta:
        model = Competition
        fields = ('url', 'id', 'name', 'full_name', 'country', 'slug', 'seasons')


class DriverSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Driver
        fields = ('url', 'id', 'last_name', 'first_name', 'year_of_birth', 'country', 'competitions')
        read_only_fields = ('competitions',)


class NestedDriverSerializer(DriverSerializer):
    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country')


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'id', 'name', 'full_name', 'competitions', 'country')


class NestedTeamSerializer(TeamSerializer):
    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'country')


#
#


class ContenderSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    driver = NestedDriverSerializer(many=False)
    teams = NestedTeamSerializer(many=True)

    # competition = CompetitionSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'id', 'driver', 'competition', 'teams')


#
class NestedContenderSerializer(ContenderSerializer):
    driver = NestedDriverSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'driver')


class SeatSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    team_details = serializers.SerializerMethodField()
    contender_details = serializers.SerializerMethodField()

    def get_team_details(self, obj):
        return TeamSerializer(instance=obj.team, many=False,
                              context=self.context).data

    def get_contender_details(self, obj):
        return ContenderSerializer(instance=obj.contender, many=False,
                                   context=self.context).data

    class Meta:
        model = Seat
        fields = ('url', 'id', 'team', 'team_details', 'contender', 'contender_details', 'current', 'seasons')


class SeatRecapSerializer(serializers.ModelSerializer):
    contender = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    def get_contender(self, obj):
        contender = obj.contender
        return {
            'id': contender.id,
            'driver': {
                'id': contender.driver.id,
                'first_name': contender.driver.first_name,
                'last_name': contender.driver.last_name
            }
        }

    def get_team(self, obj):
        team = obj.team
        return {
            'id': team.id,
            'name': team.name
        }

    class Meta:
        model = Seat
        fields = ('contender',
                  'team')


class ResultSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    seat_details = serializers.SerializerMethodField()

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
