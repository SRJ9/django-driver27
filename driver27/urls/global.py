from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.global_view, name='index'),
    url(r'^tpl/$', views.global_tpl, name='tpl'),
    url(r'^driver/(?P<driver_id>\d+)/$', views.driver_profile_view, name='driver-profile'),
    url(r'^driver/', include('driver27.urls.driver')),
    url(r'^team/(?P<team_id>\d+)/$', views.team_profile_view, name='team-profile'),
    url(r'^team/', include('driver27.urls.team')),
]
