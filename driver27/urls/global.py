from django.conf.urls import url, include

from driver27 import views

urlpatterns = [
    url(r'^driver$', views.global_rank_view, name='dr27-global-driver')
]
