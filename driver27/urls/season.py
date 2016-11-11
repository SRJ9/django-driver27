from django.conf.urls import url

from driver27 import views

urlpatterns = [
    url(r'^$', views.season_view, name='season-view'),
    url(r'^driver$', views.driver_rank_view, name='season-driver'),
    url(r'^driver/road-to-championship$', views.driver_road_view, name='season-driver-road'),
    url(r'^driver/olympic$', views.driver_olympic_view, name='season-driver-olympic'),
    url(r'^team$', views.team_rank_view, name='season-team'),
    url(r'^race$', views.race_list, name='season-race-list'),
    url(r'^race/(?P<race_id>\d+)$', views.race_view, name='season-race-view'),
    url(r'^race/(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name='season-race-rank'),
]