from django.conf.urls import url, include

from .. import views
from ..api import router

urlpatterns = [
    url(r'^global/', include('driver27.urls.global')),
    url(r'^$', views.competition_view, name='dr27-competition-list'),
    url(r'^(?P<competition_slug>[-\w\d]+)/', include('driver27.urls.competition')),
    url(r'^api/auth/', include('rest_framework.urls')),
    url(r'^api/', include(router.urls)),
]
