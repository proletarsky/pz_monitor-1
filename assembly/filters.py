import django_filters
from .models import *



class TaskFilter(django_filters.FilterSet):
	class Meta:
		model=Task
		fields = ['order','subdivision','status']		



class calendar_repair(django_filters.FilterSet):

    start_date = django_filters.DateFilter(field_name='end', lookup_expr='gte', label='Начало')
    end_date = django_filters.DateFilter(field_name='start', lookup_expr='lte', label='Конец')