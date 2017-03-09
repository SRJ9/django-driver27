"""
WSGI config for dr27_demo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from .. import import_driver27

import_driver27()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dr27_demo.settings")

application = get_wsgi_application()
