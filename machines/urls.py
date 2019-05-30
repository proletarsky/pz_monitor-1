from django.conf.urls import url, include
from . import views
from machines import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^newdata', views.api_new_data),
]
