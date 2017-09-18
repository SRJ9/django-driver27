from django.conf.urls import url, include

from .. import views
from ..api import urls_api
from ..common import DRIVER27_NAMESPACE


def driver27_urls():
    return [
        url(r'^$', views.global_view, name='view'),
        url(r'^ajax/', include('driver27.urls.ajax', namespace='dr27-ajax')),
        url(r'^global/', include('driver27.urls.global', namespace='global')),
        url(r'^api/auth/', include('rest_framework.urls')),
        url(r'^api/', include(urls_api)),
        url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/', include('driver27.urls.season', namespace='season')),
        url(r'^(?P<competition_slug>[-\w\d]+)/', include('driver27.urls.competition', namespace='competition')),
    ]


urlpatterns = [
    url(r'^', include(driver27_urls(), namespace=DRIVER27_NAMESPACE)),
]
