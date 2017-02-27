from rest_framework import routers
from .viewsets import CircuitViewSet, CompetitionViewSet, ContenderViewSet, DriverViewSet
from .viewsets import GrandPrixViewSet, RaceViewSet, ResultViewSet, SeasonViewSet
from .viewsets import SeatViewSet, TeamViewSet

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
