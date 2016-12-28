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

    class Meta:
        model = Season
        fields = ('year', 'competition', 'rounds', 'punctuation')
