from django.conf import settings
from django.utils.translation import ugettext as _


def get_init_config():
    return {
        'RECORDS': {
            'POLE': {'label': _('Pole'), 'filter': {'qualifying__exact': 1}},
            'FIRST-ROW': {'label': _('First row'), 'filter': {'qualifying__gte': 1, 'qualifying__lte': 2}},
            'COMEBACK-TO-TEN': {'label': _('Comeback to 10 firsts'), 'filter': {'qualifying__gte': 11,
                                                                                'finish__gte': 1,
                                                                                'finish__lte': 10}},
            'WIN': {'label': _('Win'), 'filter': {'finish__exact': 1}},
            'POLE-WIN': {'code': 'POLE-WIN', 'label': _('Pole and Win'), 'filter': {'qualifying__exact': 1,
                                                                                    'finish__exact': 1}},
            'POLE-WIN-FL': {'label': _('Pole, Win, Fastest lap'), 'filter': {'qualifying__exact': 1,
                                                                             'finish__exact': 1,
                                                                             'fastest_lap': True}},
            'FASTEST': {'label': _('Fastest lap'), 'filter': {'fastest_lap': True}},
            'FIRST-TWO': {'label': _('Finish 1st or 2nd'), 'filter': {'finish__gte': 1, 'finish__lte': 2},
                          'doubles': True},
            'PODIUM': {'label': _('Podium'), 'filter': {'finish__gte': 1, 'finish__lte': 3}, 'doubles': True},
            'OUT': {'label': _('OUT'), 'filter': {'retired': True}, 'doubles': True},
            'CHECKERED-FLAG': {'label': _('Checkered Flag'), 'filter': {'retired': False}, 'doubles': True},
            'TOP5': {'label': _('Top 5'), 'filter': {'finish__gte': 1, 'finish__lte': 5}, 'doubles': True},
            'TOP10': {'code': 'TOP10', 'label': _('Top 10'), 'filter': {'finish__gte': 1, 'finish__lte': 10},
                      'doubles': True},
        },
        'PUNCTUATION': {
            'F1-25': {'type': 'full', 'finish': [25, 18, 15, 12, 10, 8, 6, 4, 2, 1], 'fastest_lap': 0,
                      'label': 'F1 (25p 1st)'},
            'F1-10+8': {'type': 'full', 'finish': [10, 8, 6, 4, 3, 2, 1], 'fastest_lap': 0,
                        'label': 'F1 (10p 1st, 8p 2nd)'},
            'F1-10+6': {'type': 'full', 'finish': [10, 6, 4, 3, 2, 1], 'fastest_lap': 0,
                        'label': 'F1 (10p 1st, 6p 2nd)'},
            'MotoGP': {'type': 'full', 'finish': [25, 20, 16, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 'fastest_lap': 0,
                       'label': 'Moto GP'},
            'MotoGP-92': {'type': 'full', 'finish': [20, 15, 12, 10, 8, 6, 4, 3, 2, 1], 'fastest_lap': 0,
                          'label': 'Moto GP (only 1992)'},
            'MotoGP-88-91': {'code': 'MotoGP-88-91', 'type': 'full',
                             'finish': [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 'fastest_lap': 0,
                             'label': 'Moto GP (1988-91)'},
            'MotoGP-77-87': {'type': 'full', 'finish': [15, 12, 10, 8, 6, 6, 5, 3, 2, 1], 'fastest_lap': 0,
                             'label': 'Moto GP (1977-87)'},
        }
    }


def get_settings_config():
    config_key = 'DR27_CONFIG'
    config = {}
    if hasattr(settings, config_key):
        config.update(getattr(settings, config_key))
    return config


def get_config(param, key=None):
    config = {}
    init_config = get_init_config().get(param)
    if init_config:
        config.update(init_config)
    settings_config = get_settings_config().get(param)
    if settings_config:
        config.update(settings_config)
    if key:
        return config.get(key)
    return config
