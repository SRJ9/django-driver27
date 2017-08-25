from ..default import dr27_driver_urls
from django.conf.urls import url
from .. import views

urlpatterns = dr27_driver_urls('dr27-season') \
    + [
        url(r'^position-draw/$', views.driver_season_pos_view, name='dr27-season-position-draw'),
    ]


