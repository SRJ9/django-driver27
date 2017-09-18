from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.competition_view, name='view'),
    url(r'^driver/', include('driver27.urls.driver')),
    url(r'^team/', include('driver27.urls.team')),
]
