# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic import DetailView
from .models import Equipment, RawData, Reason, ClassifiedInterval
from .serializers import RawDataSerializer
from .forms import ReasonForm
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .parsers import CoordinatorDataParser
from .filters import EquipmentFilter
from django.utils import timezone
import re, datetime
from qsstats import QuerySetStats
from django.db.models import Avg


@permission_classes([permissions.AllowAny])
class RawDataUploadView(APIView):
    parser_classes = (CoordinatorDataParser,)

    def post(self, request, format=None):
        data = request.data
        ip = request.META.get('REMOTE_ADDR')
        for data_line in data:
            rawdata = RawData(mac_address=data_line['mac_address'],
                              channel=data_line['channel'],
                              value=data_line['value'],
                              date=data_line['time'],
                              ip=ip)
            rawdata.save()
        return Response(status=status.HTTP_201_CREATED)


# Create your views here.
class RawDataViewSet(viewsets.ModelViewSet):  # APIView, for data visualization
    # queryset = RawData.objects.all()
    serializer_class = RawDataSerializer

    def get_queryset(self):
        period = self.request.query_params.get('period', '8h')
        equipment = self.request.query_params.get('equipment')
        try:
            equip_id = int(equipment)
            mac_addr = Equipment.objects.get(pk=equip_id).xbee_mac
        except Exception:
            mac_addr = None

        # can't return useful data without mac_address so return empty queryset
        if mac_addr is None:
            return RawData.objects.none()

        delta = datetime.timedelta(hours=8)
        m = re.search(r'^(\d+)(\w)$', period)
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            if unit in ['d', 'D']:
                delta = datetime.timedelta(days=val)
            elif unit in ['m', 'M']:
                delta = datetime.timedelta(minutes=val)
            elif unit in ['w', 'W']:
                delta = datetime.timedelta(weeks=val)
            else:
                delta = datetime.timedelta(hours=val)
        start_time = timezone.now() - delta
        queryset = RawData.objects.filter(date__gte=start_time, channel='AD0', mac_address=mac_addr).order_by('date')

        return queryset


class EqipmentFilteredListView(ListView):
    model = Equipment
    template_name = 'machines/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = EquipmentFilter(self.request.GET, queryset=self.get_queryset())
        return context


class EquipmentWorksDetailView(DetailView):
    model = Equipment
    template_name = 'machines/works_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get data from RawData
        start_time = timezone.now() - datetime.timedelta(days=1)
        equip = self.object
        queryset = RawData.objects.filter(mac_address=equip.xbee_mac, channel='AD0',
                                          date__gte=start_time).order_by('date')
        # timeset = [[rdt.date, rdt.value] for rdt in queryset]
        qsstat = QuerySetStats(queryset, date_field='date', aggregate=Avg('value'))
        context['rawdata'] = qsstat.time_series(start_time, timezone.now(), interval='minutes')
        return context


def index(request):
    equipment_list = Equipment.objects.all()
    context = {
        'equipment_list': equipment_list,
        'form': ReasonForm(request.POST or None),
    }

    return render(request, 'machines/index.html', context)
