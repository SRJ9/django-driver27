from rest_framework import routers
from .viewsets import CircuitViewSet, CompetitionViewSet, DriverViewSet
from .viewsets import GrandPrixViewSet, RaceViewSet, ResultViewSet, SeasonViewSet
from .viewsets import SeatViewSet, TeamViewSet, SeatPeriodViewSet
from ..common import DRIVER27_API_NAMESPACE

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'circuits', CircuitViewSet)
router.register(r'competitions', CompetitionViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'grands-prix', GrandPrixViewSet)
router.register(r'races', RaceViewSet)
router.register(r'results', ResultViewSet)
router.register(r'seasons', SeasonViewSet)
router.register(r'seats', SeatViewSet)
router.register(r'seat-periods', SeatPeriodViewSet)
router.register(r'teams', TeamViewSet)

from django.conf.urls import url, include
urls_api = [
    url(r'^', include(router.urls, namespace=DRIVER27_API_NAMESPACE)),
]