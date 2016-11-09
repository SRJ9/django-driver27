from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.competition_view, name='competition-list'),
    url(r'^(?P<competition_slug>[-\w\d]+)$', views.competition_view, name='competition-view'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/', include('driver27.urls.season')),
]