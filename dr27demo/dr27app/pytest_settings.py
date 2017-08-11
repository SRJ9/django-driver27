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