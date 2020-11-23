from django.shortcuts import render
from .models import *


def main_page(request):
    return render(request, 'sanctuary/main_page.html')


def ip_statuses(request):
    catalog_id_get = None
    if request.GET.get('catalog_id'):
        catalog_id_get = request.GET.get('catalog_id')
    if catalog_id_get:
        all_catalogs = Catalog.objects.all()
        ip_objects_active = Object_list.objects.filter(catalog_id=catalog_id_get)
        return render(request,'sanctuary/ip_statuses.html',{'all_catalogs':all_catalogs,'ip_objects_active':ip_objects_active})
    else:
        all_catalogs = Catalog.objects.all()
        ip_objects_active = Object_list.objects.all()
        return render(request,'sanctuary/ip_statuses.html',{'all_catalogs':all_catalogs,'ip_objects_active':ip_objects_active})



