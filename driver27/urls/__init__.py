from django.conf.urls import url, include

from .. import views
from ..api import router

urlpatterns = [
    url(r'^$', views.global_view, name='dr27-global-view'),
    url(r'^global/', include('driver27.urls.global')),
    url(r'^api/auth/', include('rest_framework.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^(?P<competition_slug>[-\w\d]+)/', include('driver27.urls.competition')),
]
