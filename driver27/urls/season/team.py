from django.conf.urls import url

from driver27 import views

urlpatterns = [
    url(r'^$', views.team_rank_view, name='dr27-season-team'),
    url(r'^record$', views.team_record_stats_view, name='dr27-season-team-record-index'),
    url(r'^record/(?P<record>[-\w\d]+)$', views.team_record_stats_view, name='dr27-season-team-record'),
    url(r'^record/(?P<record>[-\w\d]+)/races$', views.team_record_races_view, name='dr27-season-team-record-races'),
    url(r'^record/(?P<record>[-\w\d]+)/doubles-in-race$', views.team_record_doubles_view,
        name='dr27-season-team-record-doubles'),
]