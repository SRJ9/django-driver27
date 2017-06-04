from django.utils.timezone import datetime  # important if using timezones
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from .common import DR27ViewSet
from .serializers import RaceSerializer, ResultSerializer, SeatSerializer, SeasonSerializer
from .serializers import CircuitSerializer, GrandPrixSerializer, CompetitionSerializer
from .serializers import TeamSerializer, DriverSerializer, SeatPeriodSerializer
from .common import get_dict_from_rank_entry, get_dict_from_team_rank_entry
from ..models import Competition, Driver, Race, Result, Season, Seat, Team, GrandPrix, Circuit, SeatPeriod
from django.db.models import Q


class CommonDetailViewSet(object):
    def get_common_detail_route(self, request, rel_model, serializer_cls, filters={}):
        obj = self.get_object()
        self.queryset = getattr(obj, rel_model).filter(**filters)
        serializer = serializer_cls(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_seat_detail_route(self, request, filter={}, exclude={}):
        """ Seat can not be directly accessed from Race """
        self.queryset = Seat.objects.filter(**filter).exclude(**exclude)
        serializer = SeatSerializer(instance=self.queryset, many=True, context={'request': request})
        return Response(serializer.data)


# ViewSets define the view behavior.
class RaceViewSet(DR27ViewSet, CommonDetailViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer

    @detail_route(methods=['get'])
    def results(self, request, pk=None):
        return self.get_common_detail_route(request, 'results', ResultSerializer)

    @detail_route(methods=['get'])
    def seats(self, request, pk=None):
        obj = self.get_object()
        return self.get_seat_detail_route(request, filter={'results__race': obj})

    @detail_route(methods=['get'], url_path='no-start-seats')
    def no_start_seats(self, request, pk=None):
        """ Seats in this season that are not part of the race """

        return self.get_common_detail_route(request, 'no_seats', SeatSerializer)


class DR27CommonCompetitionViewSet(DR27ViewSet):
    @detail_route(methods=['get'], url_path='next-race')
    def next_race(self, request, pk=None):
        obj = self.get_object()
        queryset_params = {'date__gte': datetime.today()}
        if isinstance(obj, Season):
            self.queryset = obj.races.filter(**queryset_params).first()
        elif isinstance(obj, Competition):
            queryset_params['season__competition'] = obj
            self.queryset = Race.objects.filter(**queryset_params).first()
        else:
            raise NotImplementedError('Not Implemented Method')
        serializer = RaceSerializer(instance=self.queryset, many=False, context={'request': request})
        return Response(serializer.data)


# ViewSets define the view behavior.
class SeasonViewSet(DR27CommonCompetitionViewSet, CommonDetailViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

    @detail_route(methods=['get'])
    def races(self, request, pk=None):
        return self.get_common_detail_route(request, 'races', RaceSerializer)

    @detail_route(methods=['get'])
    def seats(self, request, pk=None):
        return self.get_common_detail_route(request, 'seats', SeatSerializer)

    @detail_route(methods=['get'], url_path='no-seats')
    def no_seats(self, request, pk=None):
        """ Seats with team in season:competition but not active in season """
        return self.get_common_detail_route(request, 'no_seats', SeatSerializer)

    @detail_route(methods=['get'])
    def teams(self, request, pk=None):
        return self.get_common_detail_route(request, 'teams', TeamSerializer)

    @detail_route(methods=['get'])
    def standings(self, request, pk=None):
        season = self.get_object()
        rank = season.points_rank()
        serializer_rank = [
            get_dict_from_rank_entry(standing) for standing in rank
        ]
        return Response(serializer_rank)

    @detail_route(methods=['get'], url_path='standings-team')
    def standings_team(self, request, pk=None):
        season = self.get_object()
        rank = season.team_points_rank()
        serializer_rank = [
            get_dict_from_team_rank_entry(standing) for standing in rank
        ]
        return Response(serializer_rank)

    @detail_route(methods=['get'])
    def title(self, request, pk=None):
        season = self.get_object()
        rank = season.only_title_contenders()
        serializer_rank = [
            get_dict_from_rank_entry(standing) for standing in rank
        ]
        return Response(serializer_rank)


# ViewSets define the view behavior.
class CircuitViewSet(DR27ViewSet):
    queryset = Circuit.objects.all()
    serializer_class = CircuitSerializer


# ViewSets define the view behavior.
class GrandPrixViewSet(DR27ViewSet):
    queryset = GrandPrix.objects.all()
    serializer_class = GrandPrixSerializer


# ViewSets define the view behavior.
class CompetitionViewSet(DR27CommonCompetitionViewSet, CommonDetailViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

    @detail_route(methods=['get'])
    def teams(self, request, pk=None):
        return self.get_common_detail_route(request, 'teams', TeamSerializer)


# ViewSets define the view behavior.
class ResultViewSet(DR27ViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


# ViewSets define the view behavior.
class DriverViewSet(DR27CommonCompetitionViewSet, CommonDetailViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    @detail_route(methods=['get'])
    def seats(self, request, pk=None):
        return self.get_common_detail_route(request, 'seats', SeatSerializer)


# ViewSets define the view behavior.
class TeamViewSet(DR27ViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


# ViewSets define the view behavior.
class SeatViewSet(DR27ViewSet, CommonDetailViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer

    @detail_route(methods=['get'])
    def periods(self, request, pk=None):
        return self.get_common_detail_route(request, 'periods', SeatPeriodSerializer)


# ViewSets define the view behavior.
class SeatPeriodViewSet(DR27ViewSet):
    queryset = SeatPeriod.objects.all()
    serializer_class = SeatPeriodSerializer
