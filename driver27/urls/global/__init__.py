from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.global_view, name='dr27-global-index'),
    url(r'^rank/driver/', include('driver27.urls.global.driver')),
    url(r'^rank/team/', include('driver27.urls.global.team')),
]
