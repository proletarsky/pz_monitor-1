from django.urls import path
from . import views


urlpatterns = [
	path('main',views.main,name='main'),
    path('pdo_tasks/', views.View_pdo_tasks.as_view(), name='pdo_tasks'),
    path('pdo_create/',views.Create_task.as_view(),name='pdo_create'),
    path('pdo_update/<int:pk>',views.Update_task.as_view(),name='pdo_update'),
    path('active_tasks/',views.Active_tasks.as_view(),name='active_tasks'),
    path('task_story/',views.Task_story.as_view(),name='task_story'),
    path('report_create/',views.Create_report.as_view(),name='report_create'),
    path('view_reports/',views.View_reports.as_view(),name='view_reports'),
    path('report_view/<int:pk>',views.Report_view.as_view(),name='report_view'),
    path('report_update/<int:pk>',views.Update_report.as_view(),name ='report_update'),
    path('assembly_statistics',views.assembly_statistics,name='assembly_statistics')
]