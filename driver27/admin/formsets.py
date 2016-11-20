from django import forms
from ..models import Race
from ..models import Seat, SeatSeason
from ..models import TeamSeason

class RaceFormSet(forms.models.BaseInlineFormSet):
    model = Race

    def get_copy_race(self, copy_id):
        races = Race.objects.filter(season__pk=copy_id)
        initial = []
        for race in races:
            initial.append(
                {
                    'round': race.round,
                    'circuit': race.circuit,
                    'grand_prix': race.grand_prix
                }
            )
        return initial

    def __init__(self, *args, **kwargs):
        super(RaceFormSet, self).__init__(*args, **kwargs)
        request = self.request
        copy_id = request.GET.get('copy', None)
        if not self.initial and copy_id:
            self.initial = self.get_copy_race(copy_id)
            self.extra += len(self.initial)


class SeatSeasonFormSet(forms.models.BaseInlineFormSet):
    model = SeatSeason

    def get_seat_copy(self, copy_id):
        seats_season = Seat.objects.filter(seasons__pk=copy_id)
        initial = []
        for seat_season in seats_season:
            initial.append(
                {
                    'seat': seat_season.pk,
                }
            )
        return initial

    def __init__(self, *args, **kwargs):
        super(SeatSeasonFormSet, self).__init__(*args, **kwargs)
        request = self.request
        copy_id = request.GET.get('copy', None)
        if not self.initial and copy_id:
            self.initial = self.get_seat_copy(copy_id)
            self.extra += len(self.initial)


class TeamSeasonFormSet(forms.models.BaseInlineFormSet):
    model = TeamSeason

    def get_team_copy(self, copy_id):
        teams_season = TeamSeason.objects.filter(season__pk=copy_id)
        initial = []
        for team_season in teams_season:
            initial.append(
                {
                    'team': team_season.team,
                    'sponsor_name': team_season.sponsor_name,
                }
            )
        return initial

    def clean(self):
        delete_checked = False

        for form in self.forms:
            try:
                if form.cleaned_data and form.cleaned_data.get('DELETE'):
                    team = form.cleaned_data.get('team')
                    season = form.cleaned_data.get('season')
                    seat_check = TeamSeason.check_delete_seat_restriction(team=team, season=season)
                    if seat_check:
                        delete_checked = True
            except AttributeError:
                pass

        if delete_checked:
            raise forms.ValidationError('You cannot delete a team with seats in this season.'
                                        'Delete seats before')

    def __init__(self, *args, **kwargs):
        super(TeamSeasonFormSet, self).__init__(*args, **kwargs)
        request = self.request
        copy_id = request.GET.get('copy', None)
        if not self.initial and copy_id:
            self.initial = self.get_team_copy(copy_id)
            self.extra += len(self.initial)
