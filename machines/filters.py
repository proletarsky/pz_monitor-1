import django_filters
from django import forms
from django.db import models
from .models import Equipment, Reason, ClassifiedInterval


class EquipmentFilter(django_filters.FilterSet):
    class Meta:
        model = Equipment
        fields = [
            'workshop',
            'model',
        ]
        attrs = {'class': 'sr-only'}


# for a perspective
class ClassifiedIntervalFilter(django_filters.FilterSet):
    empty_only = django_filters.BooleanFilter(field_name='user_classification',
                                              # lookup_expr='isnull',
                                              widget=forms.CheckboxInput,
                                              label='Для указания причины',
                                              method='filter_empty_only'
                                              )

    def filter_empty_only(self, queryset, name, value):
        if value:
            return queryset.filter(user_classification__isnull=True)
        else:
            return queryset

    class Meta:
        model = ClassifiedInterval
        fields = {
            'equipment': ['exact'],
            'start': ['gte'],
        }


class StatisticsFilter(django_filters.FilterSet):
    """
    For statistics purposes
    """
    PERIODS = [
        ['прошлая неделя', 'За прошедшую неделю'],
        ['прошлая декада', 'За прошедшую декаду'],
        ['прошлый месяц', 'За прошедший месяц'],
        ['текущий месяц', 'За текущий месяц'],
        # ['период', 'Указать произвольный период'],
    ]
    periods_selector = django_filters.ChoiceFilter(choices=PERIODS, label='Период');
    start_date = django_filters.DateFilter(field_name='end', lookup_expr='gte', label='Начало')
    end_date = django_filters.DateFilter(field_name='start', lookup_expr='lte', label='Конец')

    class Meta:
        model = ClassifiedInterval
        fields = []