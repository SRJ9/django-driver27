from django.conf.urls import url, include

from .. import views
from ..api import router

urlpatterns = [
    url(r'^$', views.competition_view, name='dr27-competition-list'),
    url(r'^(?P<competition_slug>[-\w\d]+)$', views.competition_view, name='dr27-competition-view'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/', include('driver27.urls.season')),
    url(r'^api/auth/', include('rest_framework.urls')),
    url(r'^api/', include(router.urls)),


]