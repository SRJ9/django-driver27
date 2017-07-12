from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.competition_view, name='dr27-competition-view'),
    url(r'^driver/', include('driver27.urls.competition.driver')),
    url(r'^team/', include('driver27.urls.competition.team')),
    url(r'^(?P<year>\d+)/', include('driver27.urls.season')),
]
