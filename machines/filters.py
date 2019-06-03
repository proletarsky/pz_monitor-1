import django_filters
from .models import Equipment, Reason


class EquipmentFilter(django_filters.FilterSet):
    class Meta:
        model = Equipment
        fields = [
            'workshop',
            'model',
        ]
        attrs = {'class': 'sr-only'}
