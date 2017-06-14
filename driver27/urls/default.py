from django.conf.urls import url

from driver27 import views


def dr27_driver_urls(base_path):
    return [
        url(r'^$', views.driver_rank_view, name=base_path+'-driver'),
        url(r'^olympic/$', views.driver_olympic_view, name=base_path+'-driver-olympic'),
        url(r'^record/$', views.driver_record_view, name=base_path+'-driver-record-index'),
        url(r'^record/(?P<record>[-\w\d]+)/$', views.driver_record_view, name=base_path+'-driver-record'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/$', views.driver_streak_view, name=base_path+'-driver-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/actives/$', views.driver_active_streak_view,
            name=base_path+'-driver-active-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top/$', views.driver_top_streak_view,
            name=base_path+'-driver-top-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top-actives/', views.driver_top_streak_active_view,
            name=base_path+'-driver-streak-inactive'),
    ]


def dr27_race_urls(base_path):
    return [
        url(r'^$', views.race_list, name=base_path+'-race-list'),
        url(r'^(?P<race_id>\d+)$', views.race_view, name=base_path+'-race-view'),
        url(r'^(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name=base_path+'-race-rank'),
    ]


def dr27_team_urls(base_path):
    return [
        url(r'^$', views.team_rank_view, name=base_path+'-team'),
        url(r'^record$', views.team_record_stats_view, name=base_path+'-team-record-index'),
        url(r'^record/(?P<record>[-\w\d]+)$', views.team_record_stats_view, name=base_path+'-team-record'),
        url(r'^record/(?P<record>[-\w\d]+)/races$', views.team_record_races_view, name=base_path+'-team-record-races'),
        url(r'^record/(?P<record>[-\w\d]+)/doubles-in-race$', views.team_record_doubles_view,
            name=base_path+'-team-record-doubles'),
    ]