from django.urls import path
from . import views

urlpatterns = [
    path('main_page', views.main_page, name='main_page'),
    path('ip_statuses',views.ip_statuses,name='ip_statuses'),
    path('sidebar_statistics',views.sidebar_ip_statistics,name='sidebar_statistics'),
    path ('diagram_statistics',views.diagram_statistics,name='diagram_statistics'),
    path ('cpu_stat',views.cpu_stat,name='cpu_stat'),
]