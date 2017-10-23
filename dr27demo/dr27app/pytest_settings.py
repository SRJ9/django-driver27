import os
from .settings import *

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'pytest.sqlite3'),
#     }
# }

PYTEST_SETTING = True
ALLOWED_HOSTS.append('testserver')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'driver27-demo-test'

    }
}