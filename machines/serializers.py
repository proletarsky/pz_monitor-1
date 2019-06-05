from rest_framework import serializers
from machines.models import RawData


class RawDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RawData
        fields = ['mac_address', 'date', 'value']
