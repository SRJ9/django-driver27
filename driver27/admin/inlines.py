from .common import *
from .filters import *
from .formsets import *
from ..models import Contender, ContenderSeason
from ..models import Race
from ..models import Result
from ..models import Seat, SeatSeason
from ..models import Team, TeamSeason


class RaceInline(CompetitionFilterInline):
    model = Race
    extra = 1
    # readonly_fields = ('print_results_link', )
    formset = RaceFormSet
    form = AlwaysChangedModelForm


class SeatInline(CompetitionFilterInline):
    model = Seat
    extra = 1


class SeatSeasonInline(CompetitionFilterInline):
    model = SeatSeason
    ordering = ('seat',)
    formset = SeatSeasonFormSet
    form = AlwaysChangedModelForm


class ContenderInline(admin.TabularInline):
    model = Contender
    extra = 1


class CompetitionTeamInline(admin.TabularInline):
    model = Team.competitions.through
    extra = 1


class TeamSeasonInlineForm(AlwaysChangedModelForm):
    pass


class TeamSeasonInline(CompetitionFilterInline):
    model = TeamSeason
    extra = 1
    formset = TeamSeasonFormSet
    form = TeamSeasonInlineForm


class TeamInline(admin.TabularInline):
    model = Team
    extra = 1


class ResultInline(CompetitionFilterInline):
    model = Result
    extra = 1
    ordering = ('retired', 'finish', 'qualifying',)
    readonly_fields = ('points',)

    @staticmethod
    def points(obj):
        points = obj.points
        return points if points else ''

