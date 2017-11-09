from .base_settings import *

INSTALLED_APPS = \
    [
        'flat_responsive',
    ] + \
    INSTALLED_APPS + \
    [

        'memcache_status',
        'django_clear_memcache'
    ]

# Append punctuation to tests
DR27_CONFIG = {
    'PUNCTUATION': {
        'EURO':
            {
                'type': 'full',
                'finish': [12, 10, 8, 7, 6, 5, 4, 3, 2, 1],
                'fastest_lap': 0,
                'label': 'EUROVISION'
            },
        '20-TO-1':

            {
                'type': 'full',
                'finish': [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
                'fastest_lap': 0,
                'label': '20 to 1'
            },
        'QUALI-F1-25':
            {
                'type': 'full',
                'qualifying': [25, 18, 15, 12, 10, 8, 6, 4, 2, 1],
                'fastest_lap': 0,
                'label': 'F1 (25 1st) - Qualifying'
            }
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'driver27-demo-app'

    }
}