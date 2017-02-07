from .models import Competition, Contender, Driver, Race, Result, Season, Seat, Team, GrandPrix, Circuit
from rest_framework import routers, serializers, viewsets, authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django_countries.serializer_fields import CountryField


class DR27Serializer(object):
    def __init__(self, *args, **kwargs):
        self.exclude_fields = kwargs.pop('exclude_fields', None)
        super(DR27Serializer, self).__init__(*args, **kwargs)

    def get_field_names(self, declared_fields, info):
        fields = super(DR27Serializer, self).get_field_names(declared_fields, info)
        if getattr(self, 'exclude_fields', None):
            fields = tuple([x for x in fields if x not in self.exclude_fields])
        return fields


class DR27ViewSet(viewsets.ModelViewSet):
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


class GrandPrixSerializer(DR27Serializer, serializers.ModelSerializer):
    country = CountryField()

    class Meta:
        model = GrandPrix
        fields = ('url', 'id', 'country', 'name', 'first_held', 'default_circuit', 'competitions',)


class CircuitSerializer(DR27Serializer, serializers.ModelSerializer):
    country = CountryField()

    class Meta:
        model = Circuit
        fields = ('url', 'country', 'name', 'city', 'opened_in',)


class SeasonSerializer(DR27Serializer, serializers.ModelSerializer):
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
        fields = ('url', 'year', 'rounds', 'slug', 'punctuation', 'competition',
                  'competition_details', 'races', )
        read_only_fields = ('competition_details', 'races',)


class CompetitionSerializer(DR27Serializer, serializers.HyperlinkedModelSerializer):
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()
    seasons = SeasonSerializer(many=True, exclude_fields=['competition', 'competition_details', 'races'])

    class Meta:
        model = Competition
        fields = ('url', 'name', 'full_name', 'country', 'slug', 'seasons')


class DriverSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country', 'competitions')
        read_only_fields = ('competitions', )


class NestedDriverSerializer(DriverSerializer):

    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country')

#
class TeamSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'competitions', 'country')

#
class NestedTeamSerializer(TeamSerializer):

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'country')
#
#


class ContenderSerializer(serializers.HyperlinkedModelSerializer):
    driver = NestedDriverSerializer(many=False)
    teams = NestedTeamSerializer(many=True)
    # competition = CompetitionSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'driver', 'competition', 'teams')


#
class NestedContenderSerializer(ContenderSerializer):
    driver = NestedDriverSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'driver')


class SeatSerializer(serializers.ModelSerializer):
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
        fields = ('url', 'team', 'team_details', 'contender', 'contender_details', 'current', 'seasons')
#
#
# class NestedSeatSerializer(SeatSerializer):
#     class Meta:
#         model = Seat
#         fields = ('url', 'team', 'contender', 'current')
#
#


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
    # seat = SeatSerializer(many=False, read_only=True)
    seat_details = serializers.SerializerMethodField()

    def get_seat_details(self, obj):
        return SeatRecapSerializer(instance=obj.seat,
                                   many=False,
                                   context=self.context).data

    class Meta:
        model = Result
        fields = ('url',
                  'race',
                  'seat',
                  'seat_details',
                  'qualifying',
                  'finish',
                  'fastest_lap',
                  'wildcard',
                  'retired',
                  'comment')
#
#
# class NestedResultSerializer(ResultSerializer):
#
#     class Meta:
#         model = Result
#         fields = ('url', 'seat', 'qualifying', 'finish', 'fastest_lap', 'wildcard',
#                   'retired', 'comment')
#
#
# class NestedSeasonSerializer(SeasonSerializer):
#     competition = CompetitionSerializer(many=False)
#
#     class Meta:
#         model = Season
#         fields = ('url', 'year', 'competition', 'rounds', 'punctuation')
#
#


class RaceSerializer(serializers.ModelSerializer):

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
        fields = ('url', 'id', 'season', 'round',  'grand_prix', 'grand_prix_details',
                  'circuit', 'circuit_details', 'date', 'alter_punctuation')
#
#


# # ViewSets define the view behavior.
class RaceViewSet(DR27ViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer

    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        race = self.get_object()
        self.queryset = race.results.all()
        serializer = ResultSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)


# ViewSets define the view behavior.
class SeasonViewSet(DR27ViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

    @detail_route(methods=['get'])
    def races(self, request, pk=None):
        season = self.get_object()
        self.queryset = season.races.all()
        serializer = RaceSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def seats(self, request, pk=None):
        season = self.get_object()
        self.queryset = season.seats.all()
        serializer = SeatSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)


# ViewSets define the view behavior.
class CircuitViewSet(DR27ViewSet):
    queryset = Circuit.objects.all()
    serializer_class = CircuitSerializer


# ViewSets define the view behavior.
class GrandPrixViewSet(DR27ViewSet):
    queryset = GrandPrix.objects.all()
    serializer_class = GrandPrixSerializer


# ViewSets define the view behavior.
class CompetitionViewSet(DR27ViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer


# ViewSets define the view behavior.
class ResultViewSet(DR27ViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


# ViewSets define the view behavior.
class ContenderViewSet(DR27ViewSet):
    queryset = Contender.objects.all()
    serializer_class = ContenderSerializer


# ViewSets define the view behavior.
class DriverViewSet(DR27ViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


# ViewSets define the view behavior.
class TeamViewSet(DR27ViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


# ViewSets define the view behavior.
class SeatViewSet(DR27ViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'circuits', CircuitViewSet)
router.register(r'competitions', CompetitionViewSet)
router.register(r'contenders', ContenderViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'grands-prix', GrandPrixViewSet)
router.register(r'races', RaceViewSet)
router.register(r'results', ResultViewSet)
router.register(r'seasons', SeasonViewSet)
router.register(r'seats', SeatViewSet)
router.register(r'teams', TeamViewSet)
