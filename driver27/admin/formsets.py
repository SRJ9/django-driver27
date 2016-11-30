from django import forms
from ..models import Race
from ..models import Seat, SeatSeason
from ..models import TeamSeason


class RelatedWithSeasonFormSet(forms.models.BaseInlineFormSet):
    model = None
    model_attributes = []

    def get_copy(self, copy_id):
        related_objects = self.model.objects.filter(season__pk=copy_id)
        initial = []
        for x in related_objects:
            initial_x = {}
            for xa in self.model_attributes:
                initial_x[xa] = getattr(x, xa, None)
            initial.append(initial_x)
        return initial

    def __init__(self, *args, **kwargs):
        super(RelatedWithSeasonFormSet, self).__init__(*args, **kwargs)
        request = self.request
        copy_id = request.GET.get('copy', None)
        if not self.initial and copy_id:
            self.initial = self.get_copy(copy_id)
            self.extra += len(self.initial)


class RaceFormSet(RelatedWithSeasonFormSet):
    model = Race
    model_attributes = ('round', 'circuit', 'grand_prix',)


class SeatSeasonFormSet(RelatedWithSeasonFormSet):
    model = SeatSeason
    model_attributes = ('seat',)


class TeamSeasonFormSet(RelatedWithSeasonFormSet):
    model = TeamSeason
    model_attributes = ('team', 'sponsor_name',)

    def check_if_delete_team_season(self, form):
        delete_checked = False
        team = form.cleaned_data.get('team')
        season = form.cleaned_data.get('season')
        seat_check = self.model.check_delete_seat_restriction(team=team, season=season)
        if seat_check:
            delete_checked = True
        return delete_checked

    def clean(self):
        super(TeamSeasonFormSet, self).clean()
        delete_checked = False

        for form in self.forms:
            try:
                if form.cleaned_data and form.cleaned_data.get('DELETE') and not delete_checked:
                    delete_checked = self.check_if_delete_team_season(form)
            except AttributeError:
                pass

        if delete_checked:
            raise forms.ValidationError('You cannot delete a team with seats in this season.'
                                        'Delete seats before')