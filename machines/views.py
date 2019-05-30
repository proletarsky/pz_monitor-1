# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from models import Equipment, RawData
from serializers import RawDataSerializer
from .forms import ReasonForm
from rest_framework import routers, serializers, viewsets, response, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_new_data(request, format=None):
    post = request.POST
    try:
        assert post['name'] == 'xbee.analog'
        ip = request.META.get('REMOTE_ADDR')
        mac = re.findall(ur'[0-9ABCDEF:]{20,}', str(post), flags=re.U|re.I)[0]
        ch = post['ident']
        value = post['value']
        rawdata = RawData(mac_address=mac, channel=ch, value=value, ip=ip)
        rawdata.save()
    except Exception as e:
        return Response(e, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response("Created", status=status.HTTP_201_CREATED)

# Create your views here.
class RawDataViewSet(viewsets.ModelViewSet):
    queryset = RawData.objects.all()
    serializer_class = RawDataSerializer


def index(request):
    equipment_list = Equipment.objects.all()
    context = {
        'equipment_list': equipment_list,
        'form': ReasonForm(request.POST or None),
    }

    return render(request, 'machines/index.html', context)