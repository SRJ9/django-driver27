from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^driver$', views.driver_rank_view, name='dr27-competition-driver'),
    url(r'^driver/record$', views.driver_record_view, name='dr27-competition-driver-record-index'),
    url(r'^driver/record/(?P<record>[-\w\d]+)$', views.driver_record_view, name='dr27-competition-driver-record'),
]