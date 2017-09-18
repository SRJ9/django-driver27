from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.season_view, name='view'),
    url(r'^driver/position-draw/$', views.driver_season_pos_view, name='position-draw'),
    url(r'^driver/', include('driver27.urls.driver')),
    url(r'^team/', include('driver27.urls.team')),
    url(r'^race/', include('driver27.urls.season.race')),
]
