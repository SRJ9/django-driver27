from django.conf.urls import url

from driver27 import views

urlpatterns = [
    url(r'^$', views.driver_rank_view, name='dr27-season-driver'),
    url(r'^road-to-championship$', views.driver_road_view, name='dr27-season-driver-road'),
    url(r'^olympic$', views.driver_olympic_view, name='dr27-season-driver-olympic'),
    url(r'^record$', views.driver_record_view, name='dr27-season-driver-record-index'),
    url(r'^record/(?P<record>[-\w\d]+)$', views.driver_record_view, name='dr27-season-driver-record'),
]