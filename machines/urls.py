from django.conf.urls import url, include
from django.urls import path
from . import views
from machines import views
from rest_framework import routers
from .views import RawDataViewSet, EquipmentWorksDetailView

router = routers.DefaultRouter()
router.register(r'^api/rawdata', RawDataViewSet, basename='RawData')

urlpatterns = [
                  url(r'^$', views.EqipmentFilteredListView.as_view(), name='equipment-list'),
                  url(r'^accounts/', include('django.contrib.auth.urls')),
                  url(r'^register$', views.register, name='register'),
                  url(r'^newdata/', views.RawDataUploadView.as_view()),
                  url(r'graph', views.APIGraphData.as_view(), name='graph-data'),
                  url(r'^ci$', views.ClassifiedIntervalsListView.as_view(), name='classifiedinterval-list'),
                  url(r'^stats', views.StatisticsView.as_view(), name='statistics-view'),
                  path('works/<int:pk>/', views.EquipmentWorksDetailView.as_view(), name='works-detail'),
              ] + router.urls
