from .models import Competition, Contender, Driver, Race, Result, Season, Seat, Team
from rest_framework import routers, serializers, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django_countries.serializer_fields import CountryField


class DriverSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country', 'competitions')

class NestedDriverSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Driver
        fields = ('url', 'last_name', 'first_name', 'year_of_birth', 'country')


# ViewSets define the view behavior.
class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'competitions', 'country')

class NestedTeamSerializer(serializers.HyperlinkedModelSerializer):
    country = CountryField()

    class Meta:
        model = Team
        fields = ('url', 'name', 'full_name', 'country')


# ViewSets define the view behavior.
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class ContenderSerializer(serializers.HyperlinkedModelSerializer):
    driver = DriverSerializer(many=False)
    teams = TeamSerializer(many=True)

    class Meta:
        model = Contender
        fields = ('url', 'driver', 'competition', 'teams')

class NestedContenderSerializer(serializers.HyperlinkedModelSerializer):
    driver = NestedDriverSerializer(many=False)
    #teams = TeamSerializer(many=True)

    class Meta:
        model = Contender
        fields = ('url', 'driver')


# ViewSets define the view behavior.
class ContenderViewSet(viewsets.ModelViewSet):
    queryset = Contender.objects.all()
    serializer_class = ContenderSerializer


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


# ViewSets define the view behavior.
class SeatViewSet(viewsets.ModelViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer


class ResultSerializer(serializers.HyperlinkedModelSerializer):
    seat = SeatSerializer(many=False)

    class Meta:
        model = Result
        fields = ('url', 'race', 'seat', 'qualifying', 'finish', 'fastest_lap', 'wildcard',
                  'retired', 'comment')

class NestedResultSerializer(serializers.HyperlinkedModelSerializer):
    seat = NestedSeatSerializer(many=False)

    class Meta:
        model = Result
        fields = ('url', 'seat', 'qualifying', 'finish', 'fastest_lap', 'wildcard',
                  'retired', 'comment')


# ViewSets define the view behavior.
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()

    class Meta:
        model = Competition
        fields = ('url', 'name', 'full_name', 'country', 'slug')


class NestedSeasonSerializer(serializers.HyperlinkedModelSerializer):
    competition = CompetitionSerializer(many=False)
    
    class Meta:
        model = Season
        fields = ('url', 'year', 'competition', 'rounds', 'punctuation')


class RaceSerializer(serializers.HyperlinkedModelSerializer):

    results = NestedResultSerializer(many=True)
    season = NestedSeasonSerializer(many=False)

    class Meta:
        model = Race
        fields = ('url', 'season', 'round',  'date', 'alter_punctuation', 'results')


# ViewSets define the view behavior.
class RaceViewSet(viewsets.ModelViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer

    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        race = self.get_object()
        self.queryset = race.results.all()
        serializer = ResultSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)


class SeasonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Season
        fields = ('url', 'year', 'competition', 'rounds', 'punctuation', 'races')

# ViewSets define the view behavior.
class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

    @detail_route(methods=['get'])
    def races(self, request, pk=None):
        season = self.get_object()
        self.queryset = season.races.all()
        serializer = RaceSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)


# ViewSets define the view behavior.
class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

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
