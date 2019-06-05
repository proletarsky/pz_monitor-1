from django.conf.urls import url, include
from django.urls import path
from . import views
from machines import views
from rest_framework import routers
from .views import RawDataViewSet, EquipmentWorksDetailView

router = routers.DefaultRouter()
router.register(r'^api/rawdata', RawDataViewSet, base_name='RawData')

urlpatterns = [
    url(r'^$', views.EqipmentFilteredListView.as_view(), name='index'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^newdata/', views.RawDataUploadView.as_view()),
                  path('works/<int:pk>/', views.EquipmentWorksDetailView.as_view(), name='works-detail'),
              ] + router.urls
