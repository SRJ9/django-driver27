from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.race_list, name='race-list'),
    url(r'^(?P<race_id>\d+)$', views.race_view, name='race-view'),
    url(r'^(?P<race_id>\d+)/(?P<rank>[-\w\d]+)$', views.race_view, name='race-rank'),
]
