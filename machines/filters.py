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

