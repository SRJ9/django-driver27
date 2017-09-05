from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^$', views.global_view, name='dr27-global-index'),
    url(r'^tpl/$', views.global_tpl, name='dr27-global-tpl'),
    url(r'^driver/', include('driver27.urls.global.driver')),
    url(r'^team/', include('driver27.urls.global.team')),
]
