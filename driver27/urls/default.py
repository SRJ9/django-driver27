from django.conf.urls import url, include

from driver27 import views

class Driver27Urls(list):

    def __init__(self, base_name):
        self.base_name = base_name
        super(Driver27Urls, self).__init__()

    def bulk_append_urls(self, urls_list):
        for url_entry in urls_list:
            self.append_url(*url_entry)


    def append_url(self, pattern, view_name, name, kwargs=None):
        if kwargs is None:
            kwargs = {}
        url_name = self.base_name
        if name:
            url_name = '-'.join([url_name, name])
        self.append(
            url(r'^'+pattern, getattr(views, view_name), name=url_name, kwargs=kwargs)
        )

def get_base_stats_url(base_path, stat_type):
    return '{base_path}-{stat_type}'.format(base_path=base_path, stat_type=stat_type)


def _dr27_records_list(base_path, stat_type):
    base_name = get_base_stats_url(base_path, stat_type)
    record_config = {'view': stat_type + '_record_view', 'name': 'record'}
    url_pattern = Driver27Urls(base_name)
    url_pattern.bulk_append_urls(
        [
            ('$', record_config['view'], record_config['name']),
            ('seasons/$', stat_type + '_record_seasons_view', 'seasons'),
            ('streak/$', stat_type + '_streak_view', 'streak'),
            ('streak/top/$', stat_type + '_streak_view', 'top-streak', {'max_streak': True})
        ]
    )

    if stat_type == 'driver':
        url_pattern.bulk_append_urls(
            [

                ('streak/actives/$', stat_type + '_streak_view', 'active-streak', {'only_actives': True}),
                ('streak/top-actives/$', stat_type + '_streak_view', 'active-top-streak', {'only_actives': True,
                                                                                           'max_streak': True})
            ]

        )

    if stat_type == 'team':
        team_view = 'team_record_view'
        url_pattern.bulk_append_urls(
            [
                ('races/$', team_view, 'record-races', {'rank_type': 'RACES'}),
                ('doubles-in-race/$', team_view,'record-doubles', {'rank_type': 'DOUBLES'}),
            ]
        )

    return url_pattern


def _dr27_stats_urls(base_path, stat_type):
    base_name = get_base_stats_url(base_path, stat_type)
    url_pattern = Driver27Urls(base_name)
    url_pattern.bulk_append_urls(
        [
            ('$', '_rank_view', '', {'rank_model':stat_type}),
            ('seasons/$', '_rank_view', 'seasons-rank', {'rank_model': stat_type, 'by_season':True}),
            ('olympic/$', stat_type + '_olympic_view', 'olympic'),
            ('record/$', stat_type + '_record_view', 'record-index'),
        ]
    )

    url_pattern += [url(r'^record/(?P<record>[-\w\d]+)/', include(_dr27_records_list(base_path, stat_type)))]

    if stat_type == 'driver':
        url_pattern.append_url('comeback/$', 'driver_comeback_view', 'comeback')

    return url_pattern

def dr27_race_urls(base_path):
    return [
        url(r'^$', views.race_list, name=base_path+'-race-list'),
        url(r'^(?P<race_id>\d+)$', views.race_view, name=base_path+'-race-view'),
        url(r'^(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name=base_path+'-race-rank'),
    ]

def dr27_driver_urls(base_path):
    url_pattern = _dr27_stats_urls(base_path, 'driver')
    return url_pattern

def dr27_team_urls(base_path):
    url_pattern = _dr27_stats_urls(base_path, 'team')
    return url_pattern
