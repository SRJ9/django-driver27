from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.competition_view, name='competition-list'),
    url(r'^(?P<competition_slug>[-\w\d]+)$', views.competition_view, name='competition-view'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)$', views.season_view, name='season-view'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/driver$', views.driver_rank_view, name='season-driver'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/team$', views.team_rank_view, name='season-team'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/race$', views.race_list, name='season-race-list'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/race/(?P<race_id>\d+)$', views.race_view, name='season-race-view'),
    url(r'^(?P<competition_slug>[-\w\d]+)/(?P<year>\d+)/race/(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name='season-race-rank'),
]