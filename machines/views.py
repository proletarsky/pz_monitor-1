# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.views.generic import ListView
from .models import Equipment, RawData
from serializers import RawDataSerializer
from .forms import ReasonForm
from rest_framework import routers, serializers, viewsets, response, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .parsers import CoordinatorDataParser
from .filters import EquipmentFilter


# @api_view(['POST'])
# @permission_classes([permissions.AllowAny])
# def api_new_data(request, format=None):
#     if request.method == 'POST':
#         post = request.POST
#         assert post['name'] == 'xbee.analog'
#         ip = request.META.get('REMOTE_ADDR')
#         mac = re.findall(ur'[0-9ABCDEF:]{20,}', str(post), flags=re.U|re.I)[0]
#         ch = post['ident']
#         value = post['value']
#         rawdata = RawData(mac_address=mac, channel=ch, value=value, ip=ip)
#         rawdata.save()
#
#     return Response("Created", status=status.HTTP_201_CREATED)


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
class RawDataViewSet(viewsets.ModelViewSet):
    queryset = RawData.objects.all()
    serializer_class = RawDataSerializer


class EqipmentFilteredListView(ListView):
    model = Equipment
    template_name = 'machines/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = EquipmentFilter(self.request.GET, queryset=self.get_queryset())
        return context

def index(request):
    equipment_list = Equipment.objects.all()
    context = {
        'equipment_list': equipment_list,
        'form': ReasonForm(request.POST or None),
    }

    return render(request, 'machines/index.html', context)