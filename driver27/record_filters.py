from django.utils.translation import ugettext as _

DR27_RECORDS_FILTER = [
    {
        'code': 'POLE',
        'label': _('Pole'),
        'filter': {'qualifying__exact': 1}
     },
    {
        'code': 'FIRST-ROW',
        'label': _('First row'),
        'filter': {'qualifying__gte': 1, 'qualifying__lte': 2}
    },
    {
        'code': 'COMEBACK-TO-TEN',
        'label': _('Comeback to 10 firsts'),
        'filter': {'qualifying__gte': 11, 'finish__gte': 1, 'finish__lte': 10}
    },
    {
        'code': 'WIN',
        'label': _('Win'),
        'filter': {'finish__exact': 1}
    },
    {
        'code': 'POLE-WIN',
        'label': _('Pole and Win'),
        'filter': {'qualifying__exact': 1, 'finish__exact': 1}
    },
    {
        'code': 'POLE-WIN-FL',
        'label': _('Pole, Win, Fastest lap'),
        'filter': {'qualifying__exact': 1, 'finish__exact': 1, 'fastest_lap': True}
    },
    {
        'code': 'FASTEST',
        'label': _('Fastest lap'),
        'filter': {'fastest_lap': True}
    },
    {
        'code': 'FIRST-TWO',
        'label': _('Finish 1st or 2nd'),
        'filter': {'finish__gte': 1, 'finish__lte': 2},
        'team_double_filter': True
    },
    {
        'code': 'PODIUM',
        'label': _('Podium'),
        'filter': {'finish__gte': 1, 'finish__lte': 3},
        'team_double_filter': True
    },
    {
        'code': 'OUT',
        'label': _('OUT'),
        'filter': {'retired': True},
        'team_double_filter': True
    },
    {
        'code': 'FINISH',
        'label': _('Finish'),
        'filter': {'retired': False},
        'team_double_filter': True
    },
    {
        'code': 'TOP5',
        'label': _('Top 5'),
        'filter': {'finish__gte': 1, 'finish__lte': 5},
        'team_double_filter': True
    },
    {
        'code': 'TOP10',
        'label': _('Top 10'),
        'filter': {'finish__gte': 1, 'finish__lte': 10},
        'team_double_filter': True
    },

]


class TeamRecord(object):

    @staticmethod
    def is_valid(rank_type):
        return rank_type in ('BY-RACE', 'MULTIPLE')


