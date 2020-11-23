from django.urls import path
from . import views

urlpatterns = [
    path('main_page', views.main_page, name='main_page'),
    path('ip_statuses',views.ip_statuses,name='ip_statuses')
]