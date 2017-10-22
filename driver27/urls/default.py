from django.conf.urls import url, include

from driver27 import views


class Driver27ShortcutUrls(list):
    def __init__(self, base_name):
        self.base_name = base_name
        super(Driver27ShortcutUrls, self).__init__()

    def bulk_append_urls(self, urls_list):
        for url_entry in urls_list:
            self.append_url(*url_entry)

    def append_url(self, pattern, view_name, name, kwargs=None):
        if kwargs is None: kwargs = {}
        url_name = '-'.join([self.base_name, name]) if name else self.base_name
        self.append(
            url(r'^' + pattern, getattr(views, view_name), name=url_name, kwargs=kwargs)
        )


def dr27_record_urls_by_type(stat_type):
    return {
        'driver': [
            ('streak/actives/$', stat_type + '_streak_view', 'active-streak', {'only_actives': True}),
            ('streak/top-actives/$', stat_type + '_streak_view', 'active-top-streak', {'only_actives': True,
                                                                                       'max_streak': True})
        ],
        'team': [
            ('races/$', 'team_record_view', 'record-races', {'rank_type': 'RACES'}),
            ('doubles-in-race/$', 'team_record_view', 'record-doubles', {'rank_type': 'DOUBLES'}),
        ]
    }.get(stat_type)


def dr27_stats_urls(stat_type):
    url_pattern = Driver27ShortcutUrls(stat_type)
    url_pattern.bulk_append_urls(
        [
            ('$', '_rank_view', '', {'rank_model': stat_type}),
            ('seasons/$', '_rank_view', 'seasons-rank', {'rank_model': stat_type, 'by_season': True}),
            ('olympic/$', stat_type + '_olympic_view', 'olympic'),
            ('record/$', stat_type + '_record_view', 'record-index'),
        ]
    )

    if stat_type == 'driver':
        url_pattern.append_url('comeback/$', 'driver_comeback_view', 'comeback')

    return url_pattern
