from django.utils.translation import ugettext as _
from django.conf import settings

DR27_RECORD_FILTERS = [
    {'code': 'POLE', 'label': _('Pole'), 'rec_filter': {'qualifying__exact': 1}},
    {'code': 'FIRST-ROW', 'label': _('First row'), 'rec_filter': {'qualifying__gte': 1, 'qualifying__lte': 2}},
    {'code': 'COMEBACK-TO-TEN', 'label': _('Comeback to 10 firsts'),
     'rec_filter': {'qualifying__gte': 11, 'finish__gte': 1, 'finish__lte': 10}},
    {'code': 'WIN', 'label': _('Win'), 'rec_filter': {'finish__exact': 1}},
    {'code': 'POLE-WIN', 'label': _('Pole and Win'), 'rec_filter': {'qualifying__exact': 1, 'finish__exact': 1}},
    {'code': 'POLE-WIN-FL', 'label': _('Pole, Win, Fastest lap'), 'rec_filter': {'qualifying__exact': 1, 'finish__exact': 1,
                                                                             'fastest_lap': True}},
    {'code': 'FASTEST', 'label': _('Fastest lap'), 'rec_filter': {'fastest_lap': True}},
    {'code': 'FIRST-TWO', 'label': _('Finish 1st or 2nd'), 'rec_filter': {'finish__gte': 1, 'finish__lte': 2},
     'team_doubles_filter': True},
    {'code': 'PODIUM', 'label': _('Podium'), 'rec_filter': {'finish__gte': 1, 'finish__lte': 3},
     'team_doubles_filter': True},
    {'code': 'OUT', 'label': _('OUT'), 'rec_filter': {'retired': True}, 'team_doubles_filter': True},
    {'code': 'CHECKERED-FLAG', 'label': _('Checkered Flag'), 'rec_filter': {'retired': False},
     'team_doubles_filter': True},
    {'code': 'TOP5', 'label': _('Top 5'), 'rec_filter': {'finish__gte': 1, 'finish__lte': 5},
     'team_doubles_filter': True},
    {'code': 'TOP10', 'label': _('Top 10'), 'rec_filter': {'finish__gte': 1, 'finish__lte': 10},
     'team_doubles_filter': True},

]

DR27_RECORD_FILTERS_EXTEND = getattr(settings, 'DR27_RECORD_FILTERS', None)
if DR27_RECORD_FILTERS_EXTEND:
    DR27_RECORD_FILTERS.extend(DR27_RECORD_FILTERS_EXTEND)

