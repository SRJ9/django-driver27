from ..default import dr27_team_urls
from django.conf.urls import url
from driver27 import views

urlpatterns = \
    [
        url(r'^(?P<team_id>\d+)/$', views.team_profile_view, name='dr27-profile-team-view'),
    ]

urlpatterns += dr27_team_urls('dr27-global')
