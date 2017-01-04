from django.conf.urls import url

from driver27 import views

urlpatterns = [
    url(r'^$', views.race_list, name='dr27-season-race-list'),
    url(r'^(?P<race_id>\d+)$', views.race_view, name='dr27-season-race-view'),
    url(r'^(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name='dr27-season-race-rank'),
]