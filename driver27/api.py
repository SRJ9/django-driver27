from .models import Competition, Contender, Driver, Race, Result, Season, Seat, Team
from rest_framework import routers, serializers, viewsets, authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django_countries.serializer_fields import CountryField


class DR27ViewSet(viewsets.ModelViewSet):
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


class SeasonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Season
        fields = ('url', 'year', 'competition', 'rounds', 'punctuation', 'races')


class CompetitionSeasonSerializer(SeasonSerializer):

    class Meta:
        model = Season
        fields = ('url', 'year', 'rounds', 'punctuation')


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()
    seasons = CompetitionSeasonSerializer(many=True)

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


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'competitions', 'country')


class NestedTeamSerializer(TeamSerializer):

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'country')


class ContenderSerializer(serializers.HyperlinkedModelSerializer):
    driver = NestedDriverSerializer(many=False)
    teams = NestedTeamSerializer(many=True)
    competition = CompetitionSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'driver', 'competition', 'teams')


class NestedContenderSerializer(ContenderSerializer):
    driver = NestedDriverSerializer(many=False)

    class Meta:
        model = Contender
        fields = ('url', 'driver')


class SeatSerializer(serializers.HyperlinkedModelSerializer):
    team = NestedTeamSerializer(many=False)
    contender = NestedContenderSerializer(many=False)

    class Meta:
        model = Seat
        fields = ('url', 'team', 'contender', 'current', 'seasons')


class NestedSeatSerializer(SeatSerializer):
    class Meta:
        model = Seat
        fields = ('url', 'team', 'contender', 'current')


class ResultSerializer(serializers.HyperlinkedModelSerializer):
    seat = SeatSerializer(many=False)

    class Meta:
        model = Result
        fields = ('url', 'race', 'seat', 'qualifying', 'finish', 'fastest_lap', 'wildcard',
                  'retired', 'comment')


class NestedResultSerializer(ResultSerializer):

    class Meta:
        model = Result
        fields = ('url', 'seat', 'qualifying', 'finish', 'fastest_lap', 'wildcard',
                  'retired', 'comment')


class NestedSeasonSerializer(SeasonSerializer):
    competition = CompetitionSerializer(many=False)
    
    class Meta:
        model = Season
        fields = ('url', 'year', 'competition', 'rounds', 'punctuation')


class RaceSerializer(serializers.HyperlinkedModelSerializer):

    # results = NestedResultSerializer(many=True)
    season = NestedSeasonSerializer(many=False)

    class Meta:
        model = Race
        fields = ('url', 'season', 'round',  'date', 'alter_punctuation')


# ViewSets define the view behavior.
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
class CompetitionViewSet(DR27ViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer


# ViewSets define the view behavior.
class DriverViewSet(DR27ViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


# ViewSets define the view behavior.
class TeamViewSet(DR27ViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


# ViewSets define the view behavior.
class ContenderViewSet(DR27ViewSet):
    queryset = Contender.objects.all()
    serializer_class = ContenderSerializer


# ViewSets define the view behavior.
class SeatViewSet(DR27ViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer


# ViewSets define the view behavior.
class ResultViewSet(DR27ViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'competitions', CompetitionViewSet)
router.register(r'contenders', ContenderViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'races', RaceViewSet)
router.register(r'results', ResultViewSet)
router.register(r'seasons', SeasonViewSet)
router.register(r'seats', SeatViewSet)
router.register(r'teams', TeamViewSet)
