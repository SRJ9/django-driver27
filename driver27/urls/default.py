from django.conf.urls import url

from driver27 import views


def _dr27_stats_urls(base_path, stat_type):
    record_view = getattr(views, stat_type+'_record_view')
    return [
        url(r'^$', getattr(views, stat_type+'_rank_view'), name=base_path+'-'+stat_type),
        url(r'^olympic/$', getattr(views, stat_type+'_olympic_view'), name=base_path+'-'+stat_type+'-olympic'),
        url(r'^record/$', getattr(views, stat_type+'_record_view'), name=base_path+'-'+stat_type+'-record-index'),
        url(r'^record/(?P<record>[-\w\d]+)/$', record_view, name=base_path+'-'+stat_type+'-record'),
        url(r'^record/(?P<record>[-\w\d]+)/seasons/$', getattr(views, stat_type+'_record_seasons_view'),
            name=base_path+'-'+stat_type+'-seasons'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/$', getattr(views, stat_type+'_streak_view'),
            name=base_path+'-'+stat_type+'-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top/$', getattr(views, stat_type+'_top_streak_view'),
            name=base_path+'-'+stat_type+'-top-streak'),
    ]


def dr27_driver_urls(base_path):
    url_pattern = _dr27_stats_urls(base_path, 'driver')
    url_pattern += [
        url(r'^record/(?P<record>[-\w\d]+)/streak/actives/$', views.driver_active_streak_view,
            name=base_path+'-driver-active-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top-actives/', views.driver_top_streak_active_view,
            name=base_path+'-driver-active-top-streak'),
    ]
    return url_pattern


def dr27_race_urls(base_path):
    return [
        url(r'^$', views.race_list, name=base_path+'-race-list'),
        url(r'^(?P<race_id>\d+)$', views.race_view, name=base_path+'-race-view'),
        url(r'^(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name=base_path+'-race-rank'),
    ]


def dr27_team_urls(base_path):
    url_pattern = _dr27_stats_urls(base_path, 'team')
    url_pattern += [
        url(r'^record/(?P<record>[-\w\d]+)/races/$', views.team_record_races_view,
            name=base_path + '-team-record-races'),
        url(r'^record/(?P<record>[-\w\d]+)/doubles-in-race/$', views.team_record_doubles_view,
            name=base_path + '-team-record-doubles'),
    ]
    return url_pattern
