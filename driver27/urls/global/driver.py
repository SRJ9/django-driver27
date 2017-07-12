from ..default import dr27_driver_urls
from django.conf.urls import url
from driver27 import views

driver_path = 'dr27-global'

urlpatterns = \
    [
        url(r'^(?P<driver_id>\d+)/$', views.driver_profile_view, name='dr27-profile-view'),
        url(r'^record-redir/$', views.driver_record_redirect_view, name='dr27-driver-record-redir')
    ]
urlpatterns += dr27_driver_urls(driver_path)
