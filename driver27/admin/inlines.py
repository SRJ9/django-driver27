from .common import *
from .filters import *
from .formsets import *
from ..models import ContenderSeason
from ..models import Race
from ..models import Result
from ..models import Seat, SeatPeriod
from ..models import Team, TeamSeason


class RaceInlineForm(AlwaysChangedModelForm):
    class Meta:
        widgets = {
            'grand_prix': GrandPrixWidget,
        }


class RaceInline(CompetitionFilterInline):
    model = Race
    extra = 1
    # readonly_fields = ('print_results_link', )
    formset = RaceFormSet
    form = RaceInlineForm


class SeatInline(CompetitionFilterInline):
    model = Seat
    extra = 1



# class CompetitionTeamInline(admin.TabularInline):
#     model = Team.competitions.through
#     extra = 1


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


class SeatPeriodInline(admin.TabularInline):
    model = SeatPeriod
    extra = 2
