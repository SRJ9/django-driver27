from .common import *
from .filters import *
from .formsets import *
from ..models import Contender
from ..models import Race
from ..models import Seat, SeatSeason
from ..models import Team, TeamSeason


class RaceInline(CommonRaceAdmin, CompetitionFilterInline):
    model = Race
    extra = 1
    readonly_fields = ('print_results_link', )
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
