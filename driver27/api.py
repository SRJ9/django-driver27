from .models import Competition, Season
from rest_framework import routers, serializers, viewsets
from django_countries.serializer_fields import CountryField


class SeasonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Season
        fields = ('year', 'competition', 'round', 'punctuation')


# ViewSets define the view behavior.
class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer


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
router.register(r'seasons', SeasonViewSet)
