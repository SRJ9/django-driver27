from django.conf import settings

DRIVER27_PUNCTUATION = [
    {
        'code': 'F1-25',
        'type': 'full',
        'finish': [25,18,15,12,10,8,6,4,2,1],
        'fastest_lap': 0,
        'label': 'F1 (25p 1st)'
    },
    {
        'code': 'F1-10+8',
        'type': 'full',
        'finish': [10, 8, 6, 4, 3, 2, 1],
        'fastest_lap': 0,
        'label': 'F1 (10p 1st, 8p 2nd)'
    },
    {
        'code': 'F1-10+6',
        'type': 'full',
        'finish': [10, 6, 4, 3, 2, 1],
        'fastest_lap': 0,
        'label': 'F1 (10p 1st, 6p 2nd)'
    },
    {
        'code': 'MotoGP',
        'type': 'full',
        'finish': [25,20,16,13,11,10,9,8,7,6,5,4,3,2,1],
        'fastest_lap': 0,
        'label': 'Moto GP'
    }
]

DRIVER27_PUNCTUATION_EXTEND = getattr(settings, 'DRIVER27_PUNCTUATION', None)
if DRIVER27_PUNCTUATION_EXTEND:
    DRIVER27_PUNCTUATION.extend(DRIVER27_PUNCTUATION_EXTEND)