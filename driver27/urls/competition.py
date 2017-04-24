from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^driver$', views.driver_rank_view, name='dr27-competition-driver'),
    url(r'^driver/record$', views.driver_record_view, name='dr27-competition-driver-record-index'),
    url(r'^driver/record/(?P<record>[-\w\d]+)$', views.driver_record_view, name='dr27-competition-driver-record'),
    url(r'^driver/record/(?P<record>[-\w\d]+)/streak$', views.driver_streak_view, name='dr27-competition-driver-streak'),
    url(r'^team$', views.team_rank_view, name='dr27-competition-team'),
    url(r'^team/record$', views.team_record_stats_view, name='dr27-competition-team-record-index'),
    url(r'^team/record/(?P<record>[-\w\d]+)$', views.team_record_stats_view, name='dr27-competition-team-record'),
    url(r'^team/record/(?P<record>[-\w\d]+)/races$', views.team_record_races_view, name='dr27-competition-team-record-races'),
    url(r'^team/record/(?P<record>[-\w\d]+)/doubles-in-race$', views.team_record_doubles_view,
        name='dr27-competition-team-record-doubles'),


]