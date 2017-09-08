from django.conf.urls import url, include

from .. import views_ajax as views
from ..api import urls_api

urlpatterns = [
    url(r'^standing/$', views.standing_view, name='standing'),
]
