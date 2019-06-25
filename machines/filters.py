import django_filters
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
    class Meta:
        model = ClassifiedInterval
        fields = [
            'start',
            'end',
        ]
