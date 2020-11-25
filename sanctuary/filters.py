import django_filters
from django import forms
from django.db import models
from .models import Object_list, Sidebar_statistics



class calendar_sanctuary(django_filters.FilterSet):

    start_date = django_filters.DateFilter(field_name='end', lookup_expr='gte', label='Начало')
    end_date = django_filters.DateFilter(field_name='start', lookup_expr='lte', label='Конец')
