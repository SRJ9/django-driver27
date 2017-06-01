from django import forms
from ..models import Race
from ..models import Seat
from ..models import TeamSeason


class RelatedWithSeasonFormSet(forms.models.BaseInlineFormSet):
    pass
    # model = None
    # model_attributes = []
    #
    # def get_copy(self, copy_id):
    #     related_objects = self.model.objects.filter(season__pk=copy_id)
    #     initial = []
    #     for x in related_objects:
    #         initial_x = {}
    #         for xa in self.model_attributes:
    #             initial_x[xa] = getattr(x, xa, None)
    #         initial.append(initial_x)
    #     return initial
    #
    # def __init__(self, *args, **kwargs):
    #     super(RelatedWithSeasonFormSet, self).__init__(*args, **kwargs)
    #     request = self.request
    #     copy_id = request.GET.get('copy')
    #     if not self.initial and copy_id:
    #         self.initial = self.get_copy(copy_id)
    #         self.extra += len(self.initial)


class RaceFormSet(RelatedWithSeasonFormSet):
    model = Race
    # model_attributes = ('round', 'circuit', 'grand_prix',)


class TeamSeasonFormSet(RelatedWithSeasonFormSet):
    model = TeamSeason
