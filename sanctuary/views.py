from django.shortcuts import render
from .models import *
import datetime
from .filters import calendar_sanctuary


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


def sidebar_ip_statistics(request):
    all_catalogs = Catalog.objects.all()

    catalog_id_param = tuple(x for x in range(0,20,1))
    start_interval = '2020-10-25'
    now =datetime.datetime.now().date()
    end_interval = str(now.year)+'-'+str(now.month)+'-'+(str(now.day) if len(str(now.day))>=2 else '0'+str(now.day))

    if request.GET.get('catalog_id_param'):
        catalog_id_param = request.GET.get('catalog_id_param'),
    if request.GET.get('start_date'):
        start_interval=request.GET.get('start_date')
    if request.GET.get('end_date'):
        end_interval=request.GET.get('end_date')

    object_list = Object_list.objects.all()
    for x in object_list:
        stats = Sidebar_statistics.objects.filter(ip_object_id=x.id).order_by('-id')
        now = datetime.datetime.now()
        if stats:
            if len(stats)>1:
                b=stats[0]
                b.de_facto=datetime.datetime(year=now.year,month=now.month,day=now.day,hour=now.hour,minute=now.minute)-datetime.datetime(year=b.start_date.year,month=b.start_date.month,day=b.start_date.day,hour=b.start_time.hour,minute=b.start_time.minute)
                b.save()
                for y in range(1,len(stats),1):
                    a=stats[y]
                    a.de_facto=datetime.datetime(year=a.end_date.year,month=a.end_date.month,day=a.end_date.day,hour=a.end_time.hour,minute=a.end_time.minute)- datetime.datetime(year=a.start_date.year,month=a.start_date.month,day=a.start_date.day,hour=a.start_time.hour,minute=a.start_time.minute)
                    a.save()
            elif len(stats)==1:
                b=stats[0]
                b.de_facto=datetime.datetime(year=now.year,month=now.month,day=now.day,hour=now.hour,minute=now.minute)-datetime.datetime(year=b.start_date.year,month=b.start_date.month,day=b.start_date.day,hour=b.start_time.hour,minute=b.start_time.minute)
                b.save()
        else:
            continue
    sql_query = Sidebar_statistics.objects.raw('''select
                                                    1 as id,ip_object_id,
                                                    coalesce(sum(case when a.status=True then de_facto end),'0:00:00') as work,
                                                    coalesce(sum(case when a.status=False then de_facto end),'0:00:00') as crush,
                                                    extract (epoch from(coalesce(sum(case when a.status=True then de_facto end),'0:00:00')))as ep_work,
                                                    extract (epoch from(coalesce(sum(case when a.status=False then de_facto end),'0:00:00'))) as ep_crush
                                                    from sanctuary_sidebar_statistics a
                                                    join sanctuary_object_list b on a.ip_object_id=b.id
                                                    where b.catalog_id in %(catalog_id_param)s and start_date >= %(start_interval)s and coalesce(end_date,current_date)<=%(end_interval)s                                 				
                                                    group by ip_object_id 
                                                     ''',params = {'catalog_id_param':catalog_id_param,'start_interval':start_interval,'end_interval':end_interval})
    filter = calendar_sanctuary(0,queryset=Object_list.objects.all())
    return render(request,'sanctuary/sidebar_statistics.html',{'sql_query':sql_query,'all_catalogs':all_catalogs,'filter':filter,'start_interval':start_interval,'end_interval':end_interval,'catalog_id_param':catalog_id_param[0]})

def diagram_statistics(request):
    
    all_catalogs = Catalog.objects.all()

    catalog_id_param = tuple(x for x in range(0,20,1))
    start_interval = '2020-10-25'
    now =datetime.datetime.now().date()
    end_interval = str(now.year)+'-'+str(now.month)+'-'+(str(now.day) if len(str(now.day))>=2 else '0'+str(now.day))

    if request.GET.get('catalog_id_param'):
        catalog_id_param = request.GET.get('catalog_id_param'),
    if request.GET.get('start_date'):
        start_interval=request.GET.get('start_date')
    if request.GET.get('end_date'):
        end_interval=request.GET.get('end_date')
    sql_query = Sidebar_statistics.objects.raw('''select
                                                    1 as id,ip_object_id,count(*) as count
                                                    from sanctuary_sidebar_statistics a
                                                    join sanctuary_object_list b on a.ip_object_id=b.id
                                                    where b.catalog_id in %(catalog_id_param)s and start_date >= %(start_interval)s and coalesce(end_date,current_date)<=%(end_interval)s 
                                                    and  a.status=False                           				
                                                    group by ip_object_id
                                                     ''',params = {'catalog_id_param':catalog_id_param,'start_interval':start_interval,'end_interval':end_interval})
    filter = calendar_sanctuary(0,queryset=Object_list.objects.all())
    return render(request,'sanctuary/diagram_statistics.html',{'sql_query':sql_query,'all_catalogs':all_catalogs,'filter':filter,'start_interval':start_interval,'end_interval':end_interval,'catalog_id_param':catalog_id_param[0]})


def cpu_stat(request):
    all_objects = Object_list.objects.filter(is_in_monitoring_cpu=True).order_by('-id')
    return render(request,'sanctuary/cpu_stat.html',{'all_objects':all_objects})

