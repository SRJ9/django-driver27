from django.conf.urls import url

from driver27 import views

urlpatterns = [
    url(r'^$', views.season_view, name='season-view'),
    url(r'^driver$', views.driver_rank_view, name='season-driver'),
    url(r'^driver/road-to-championship$', views.driver_road_view, name='season-driver-road'),
    url(r'^driver/olympic$', views.driver_olympic_view, name='season-driver-olympic'),
    url(r'^driver/record$', views.driver_record_view, name='season-driver-record-index'),
    url(r'^driver/record/(?P<record>[-\w\d]+)$', views.driver_record_view, name='season-driver-record'),
    url(r'^team$', views.team_rank_view, name='season-team'),
    url(r'^team/record$', views.team_record_stats_view, name='season-team-record-index'),
    url(r'^team/record/(?P<record>[-\w\d]+)$', views.team_record_stats_view, name='season-team-record'),
    url(r'^team/record/(?P<record>[-\w\d]+)/races$', views.team_record_races_view, name='season-team-record-races'),
    url(r'^team/record/(?P<record>[-\w\d]+)/doubles-in-race$', views.team_record_doubles_view,
        name='season-team-record-doubles'),
    url(r'^race$', views.race_list, name='season-race-list'),
    url(r'^race/(?P<race_id>\d+)$', views.race_view, name='season-race-view'),
    url(r'^race/(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name='season-race-rank'),
]