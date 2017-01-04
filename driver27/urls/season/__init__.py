from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.season_view, name='dr27-season-view'),
    url(r'^driver/', include('driver27.urls.season.driver')),
    url(r'^team/', include('driver27.urls.season.team')),
    url(r'^race/', include('driver27.urls.season.race')),
]
