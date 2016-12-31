from .models import Competition, Race, Season
from rest_framework import routers, serializers, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from django_countries.serializer_fields import CountryField


class RaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Race
        fields = ('season', 'round', 'round', 'date', 'alter_punctuation')


# ViewSets define the view behavior.
class RaceViewSet(viewsets.ModelViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer


class SeasonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Season
        fields = ('year', 'competition', 'rounds', 'punctuation', 'races')


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


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    # https://github.com/SmileyChris/django-countries/issues/106
    country = CountryField()

    class Meta:
        model = Competition
        fields = ('name', 'full_name', 'country', 'slug')


# ViewSets define the view behavior.
class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'competitions', CompetitionViewSet)
router.register(r'races', RaceViewSet)
router.register(r'seasons', SeasonViewSet)
