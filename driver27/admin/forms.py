from django.db.models.fields import BLANK_CHOICE_DASH
from .common import *
from ..punctuation import get_punctuation_label_dict
from ..models import Season


class SeasonAdminForm(AlwaysChangedModelForm):
    def __init__(self, *args, **kwargs):
        super(SeasonAdminForm, self).__init__(*args, **kwargs)
        punctuation_choices = get_punctuation_label_dict()
        self.fields['punctuation'] = forms.ChoiceField(choices=BLANK_CHOICE_DASH + list(punctuation_choices),
                                                       initial=None)
        self.fields['rounds'].help_text = 'If \'rounds\' are not empty, only the best (rounds) results will be ' \
                                          'counted for driver points'

    class Meta:
        model = Season
        fields = ('year', 'competition', 'rounds', 'punctuation')


class RaceAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'grand_prix': GrandPrixWidget,
        }
