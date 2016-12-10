from django.utils.translation import ugettext as _

DR27_RECORDS_FILTER = [
    {
        'code': 'POLE',
        'label': _('Pole'),
        'filter': {'qualifying__exact': 1}
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
        'code': 'PODIUM',
        'label': _('Podium'),
        'filter': {'finish__gte': 1, 'finish__lte': 3}
    },
    {
        'code': 'OUT',
        'label': _('OUT'),
        'filter': {'retired': True}
    },
    {
        'code': 'TOP5',
        'label': _('Top 5'),
        'filter': {'finish__gte': 1, 'finish__lte': 5}
    },

]