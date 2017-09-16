from django.conf.urls import url

from driver27 import views


def _dr27_stats_urls(base_path, stat_type):
    base_name = '{base_path}-{stat_type}'.format(base_path=base_path, stat_type=stat_type)
    rank_kw = {'rank_model': stat_type}
    rank_season_kw = {'rank_model': stat_type, 'by_season': True}
    url_pattern = [
        url(r'^$', views._rank_view, name=base_name, kwargs=rank_kw),
        url(r'^seasons/$', views._rank_view, name=base_name + '-seasons-rank', kwargs=rank_season_kw),
        url(r'^olympic/$', getattr(views, stat_type+'_olympic_view'), name=base_name + '-olympic'),
        url(r'^record/$', getattr(views, stat_type + '_record_view'), name=base_name + '-record-index'),

        url(r'^record/(?P<record>[-\w\d]+)/seasons/$', getattr(views, stat_type+'_record_seasons_view'),
            name=base_name+'-seasons'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/$', getattr(views, stat_type+'_streak_view'),
            name=base_name+'-streak'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top/$', getattr(views, stat_type+'_streak_view'),
            name=base_name+'-top-streak', kwargs={'max_streak': True}),
    ]

    if stat_type == 'driver':
        record_view = getattr(views, stat_type+'_record_view')
        url_pattern += [
            url(r'^record/(?P<record>[-\w\d]+)/$', record_view, name=base_name+'-record'),
        ]

    return url_pattern


def dr27_driver_urls(base_path):
    url_pattern = _dr27_stats_urls(base_path, 'driver')
    url_pattern += [
        url(r'^comeback/$', views.driver_comeback_view, name=base_path+'-driver-comeback'),
        url(r'^record/(?P<record>[-\w\d]+)/streak/actives/$', views.driver_streak_view,
            name=base_path+'-driver-active-streak', kwargs={'only_actives': True}),
        url(r'^record/(?P<record>[-\w\d]+)/streak/top-actives/', views.driver_streak_view,
            name=base_path+'-driver-active-top-streak', kwargs={'only_actives': True, 'max_streak': True}),
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

        url(r'^record/(?P<record>[-\w\d]+)/$', views.team_record_view,
            name=base_path + '-team-record'),
        url(r'^record/(?P<record>[-\w\d]+)/races/$', views.team_record_view,
            name=base_path + '-team-record-races', kwargs={'rank_type': 'RACES'}),
        url(r'^record/(?P<record>[-\w\d]+)/doubles-in-race/$', views.team_record_view,
            name=base_path + '-team-record-doubles', kwargs={'rank_type': 'DOUBLES'}),
    ]
    return url_pattern
