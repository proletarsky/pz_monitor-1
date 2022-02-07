# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
from statistics import mean

from django.forms import fields
from django.forms.models import inlineformset_factory
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render
from django.urls.base import reverse_lazy
from django.utils.dateparse import parse_datetime, parse_date
from django.http import Http404
from django.http.response import HttpResponse
from django.views.generic import ListView, View
from django.views.generic import DetailView, UpdateView
from .models import Equipment, RawData, Reason, ClassifiedInterval, GraphicsData, Area, Workshop, Repairer, \
    Repair_rawdata, Complex, Repair_reason, Repair_statistics, Repairer_master_reason, Repair_history, Minute_interval, \
    Hour_interval, Trinity_interval
from .serializers import RawDataSerializer
from .forms import ReasonForm, ClassifiedIntervalFormSet, EquipmentDetailForm
from rest_framework import viewsets, permissions, status, authentication
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .parsers import CoordinatorDataParser
from .filters import EquipmentFilter, ClassifiedIntervalFilter, StatisticsFilter, calendar_repair, ReportFilter
from django.utils import timezone, dateparse
import re, datetime
from .helpers import prepare_data_for_google_charts_bar, get_ci_data_timeline
from qsstats import QuerySetStats
from django.db.models import Avg
from .forms import UserRegistrationForm, Repairform
from django.shortcuts import redirect
from django.http import JsonResponse
from .de_facto_time_interval import get_de_facto_time, chill_days
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from .utils.ellipsis_paginator import EllipsisPaginator
from .utils.stats_report import get_previous_week_report


# import logging
#
# logger = logging.getLogger(__name__)


def main(request):
    return render(request, 'machines/main.html')


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
    template_name = 'machines/equipment_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = EquipmentFilter(self.request.GET,
                                            queryset=self.get_queryset().filter(is_in_monitoring=True))
        context['graph_data'] = get_ci_data_timeline()
        context['workshops'] = Workshop.objects.all()
        context['areas'] = Area.objects.all()

        if "area" in self.request.GET and self.request.GET['area'] == "9":
            if "workshop" not in self.request.GET or self.request.GET['workshop'] == "" or self.request.GET[
                'workshop'] == "26":
                context['gap_instruments'] = True
            else:
                context['gap_instruments'] = False
        return context


class EquipmentWorksDetailView(UpdateView):
    """
    View for updating classified intervals
    """
    model = Equipment
    # fields = ['model']
    form_class = EquipmentDetailForm
    # queryset =

    template_name = 'machines/works_detail.html'
    success_url = reverse_lazy('equipment-list')

    def __init__(self, *args, **kwargs):
        super(EquipmentWorksDetailView, self).__init__(*args, **kwargs)
        self.filter_date = timezone.localdate()
        self.has_changed = False

    def get_initial(self):
        self.get_filter_date()
        return {'date': self.filter_date}

    def get_filter_date(self):
        try:
            if self.request.GET:
                str_date = self.request.GET['date']
                self.filter_date = parse_date(str_date)
            else:
                str_date = self.request.POST['date']
                self.filter_date = parse_date(str_date)

            if self.filter_date > timezone.localdate():
                self.filter_date = timezone.localdate()
        except Exception as e:
            print(e)
            self.filter_date = timezone.localdate()

    def get_context_data(self, **kwargs):
        context = super(EquipmentWorksDetailView, self).get_context_data(**kwargs)

        # check rights to be sure that user is operator
        user = self.request.user
        if user.groups.filter(name='Оператор') or user.is_superuser:
            context['user_can_update'] = True

        # try to use as filter
        if (timezone.localdate() - self.filter_date).days <= 0:
            self.filter_date = timezone.localdate()
            end_time = timezone.now()
            start_time = datetime.datetime(year=timezone.now().date().year, month=timezone.now().date().month,
                                           day=timezone.now().date().day, hour=0,
                                           minute=0)  # - datetime.timedelta(days=1)
        else:
            start_time = timezone.make_aware(datetime.datetime.combine(self.filter_date, datetime.datetime.min.time()))
            end_time = start_time + datetime.timedelta(days=1)

        # date_ctl = forms.DateForm
        context['filter'] = self.filter_date

        # working with data
        # start_time = timezone.now() - datetime.timedelta(days=1)
        interval_qs = ClassifiedInterval.objects.filter(((Q(start__lt=start_time) & Q(end__gte=start_time)) |
                                                         (Q(start__lt=end_time) & Q(end__gte=end_time)) |
                                                         (Q(start__gte=start_time) & Q(end__lt=end_time))) &
                                                        Q(equipment=self.object)).order_by('end')

        # get data from RawData
        # queryset = RawData.objects.filter(mac_address=self.object.xbee_mac, channel='AD0',
        #                                  date__gte=start_time, date__lt=end_time).order_by('date')
        # qsstat = QuerySetStats(queryset, date_field='date', aggregate=Avg('value'))
        # context['rawdata'] = qsstat.time_series(start_time, end_time, interval='minutes')

        graph_qs = GraphicsData.objects.filter(equipment=self.object, date__gte=start_time,
                                               date__lte=end_time).order_by('date')

        context['rawdata'] = [[gd.date, gd.value] for gd in graph_qs]

        start_new_limits = datetime.datetime(year=self.filter_date.year, month=self.filter_date.month,
                                             day=self.filter_date.day, hour=0, minute=0)  # ,second=0)
        end_new_limits = start_new_limits + datetime.timedelta(days=1)

        if self.object.problem_machine:
            context['minute_interval'] = Minute_interval.objects.filter(equipment_id=self.object.id,
                                                                        starting__gte=start_new_limits,
                                                                        ending__lte=end_new_limits).order_by('id')
            context['hour_interval'] = Hour_interval.objects.filter(equipment_id=self.object.id,
                                                                    starting__gte=start_new_limits,
                                                                    ending__lte=end_new_limits).order_by('id')
            context['trinity_interval'] = Trinity_interval.objects.filter(equipment_id=self.object.id,
                                                                          starting__gte=start_new_limits,
                                                                          ending__lte=end_new_limits).order_by('id')
        context['new_algoritm'] = self.object.problem_machine
        context['reason_list'] = Reason.objects.filter(is_operator=True)

        if self.request.POST:
            if self.object.problem_machine:
                if self.request.POST.get('reason_id') and self.request.POST.get('hour_id'):
                    hour_id = self.request.POST.get('hour_id')
                    reason_id = self.request.POST.get('reason_id')
                    reason = Reason.objects.get(id=reason_id)
                    hour = Hour_interval.objects.get(id=hour_id)
                    end_interval = Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=True,
                                                                starting__gte=hour.ending, starting__date=(
                                hour.starting + datetime.timedelta(hours=3)).date()).order_by('id')
                    if end_interval:
                        end_interval = end_interval[0:1:1][0]

                    else:
                        last_object = Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=False,
                                                                   starting__date=(hour.starting + datetime.timedelta(
                                                                       hours=3)).date()).order_by('-id')[0:1:1][0]
                        if last_object.id == hour.id:
                            end_interval = hour
                        else:
                            end_interval = \
                                Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=False,
                                                             starting__date=(hour.starting + datetime.timedelta(
                                                                 hours=3)).date(), starting__gte=hour.ending).order_by(
                                    '-id')[0:1:1][0]

                    start_interval = Hour_interval.objects.filter(equipment=hour.equipment, work_check=True,
                                                                  starting__date=(hour.starting + datetime.timedelta(
                                                                      hours=3)).date(),
                                                                  ending__lte=hour.starting).order_by('-id')
                    if start_interval:
                        start_interval = start_interval[0:1:1][0]

                    else:
                        fisrt_object = Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=False,
                                                                    starting__date=(hour.starting + datetime.timedelta(
                                                                        hours=3)).date()).order_by('id')[0:1:1][0]
                        if fisrt_object.id == hour.id:
                            start_interval = hour
                        else:
                            start_interval = \
                                Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=False,
                                                             starting__lte=hour.starting, starting__date=(
                                            hour.starting + datetime.timedelta(hours=3)).date()).order_by('id')[0:1:1][
                                    0]

                    if end_interval and start_interval:
                        need_objects = Hour_interval.objects.filter(equipment_id=hour.equipment.id, work_check=False,
                                                                    id__gte=start_interval.id, id__lte=end_interval.id,
                                                                    user_reason__isnull=True)
                        for x in need_objects:
                            x.user_reason = reason
                            x.save()
                        hour.user_reason = reason
                        hour.save()
                    else:
                        hour.user_reason = reason
                        hour.save()
            context['intervals'] = ClassifiedIntervalFormSet(self.request.POST, queryset=interval_qs)
        else:
            context['intervals'] = ClassifiedIntervalFormSet(queryset=interval_qs)

        return context

    def form_valid(self, form):
        form = EquipmentDetailForm(self.request.POST)

        if form.is_valid():
            self.filter_date = form.cleaned_data.get('date', timezone.localdate())

        # if self.filter_date != form.cleaned_data.get('date'):
        #     print('WTF???? {0} not equals {1}'.format(self.filter_date, form.cleaned_data.get('date')))
        #     self.filter_date = timezone.localdate()

        self.has_changed = form.has_changed()
        context = self.get_context_data()
        intervals = context['intervals']
        with transaction.atomic():
            self.object = form.save(commit=False)
            if intervals.is_valid():
                cis = intervals.save(commit=False)
                for ci in cis:
                    ci.user = self.request.user
                    ci.save()

        return super(EquipmentWorksDetailView, self).form_valid(form)

    def get_success_url(self):
        if self.has_changed:
            return '?date={0}'.format(self.filter_date)
        else:
            return reverse_lazy('equipment-list')


def index(request):
    equipment_list = Equipment.objects.all()
    context = {
        'equipment_list': equipment_list,
        'form': ReasonForm(request.POST or None),
    }

    return render(request, 'machines/equipment_list.html', context)


def statistics1(request):
    return render(request, 'machines/statistics1.html')


def register(request):
    """
    User registration view
    :param request:
    :return:
    """
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # —оздание пользовател€тел€, но пока не сохран€ем его
            new_user = user_form.save(commit=False)
            # ”станвока парол€
            new_user.set_password(user_form.cleaned_data['password'])
            # —охранение пользовател
            new_user.save()
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})


@permission_classes([permissions.AllowAny])
class APIGraphData(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        """
        return data for graph
        """
        try:

            obj_id = request.query_params.get('equipment', 0)
            end_date = request.query_params.get('end_date', timezone.now())
            start_date = request.query_params.get('start_date')

            equip = Equipment.objects.filter(id=obj_id).first()
            if isinstance(end_date, str):
                end_date = parse_datetime(end_date) or parse_date(end_date)
            if start_date is None:
                start_date = end_date - datetime.timedelta(days=1)

            qs = RawData.objects.filter(mac_address=equip.xbee_mac, channel=equip.main_channel).order_by('date')
            qss = QuerySetStats(qs=qs, date_field='date', aggregate=Avg('value'))
            time_series = qss.time_series(start_date, end_date, interval='minutes')

            data = {'equipment': str(equip), 'end_date': end_date, 'ts': time_series}

        except Exception as e:
            raise Http404('Error in parameters')

        return Response(data)


# добавление по печке Шабанов Р.Д 20.07.2020
# def furnace_one(request):
#    data = RawData.objects.filter(mac_address='DC:A6:32:6E:1B:95:001').order_by('date')
#    context={'rawdata':data,}
#    #return render(request,'furnace_one.html',context)
#    return render(request, 'machines/furnace_one.html', context)


class ClassifiedIntervalsListView(ListView):
    model = ClassifiedInterval
    # paginate_by = 20
    template_name = 'machines/classifiedintervals_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        ci_filter = ClassifiedIntervalFilter(self.request.GET,
                                             queryset=ClassifiedInterval.objects.filter(
                                                 automated_classification__is_working=False,
                                                 equipment__is_in_monitoring=True).order_by('start'))
        paginator = Paginator(ci_filter.qs, 15)
        page = self.request.GET.get('page')
        objs = paginator.get_page(page)
        context['filter'] = ci_filter
        context['filtered_objects'] = objs
        return context


class StatisticsView(ListView):
    model = ClassifiedInterval
    template_name = 'machines/statistics.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return_machine = 0
        return_workshop = 0
        workshop_id = [x.workshop_number for x in Workshop.objects.all()]
        if self.request.GET.get('workshop_id'):
            workshop_id = self.request.GET.get('workshop_id'),
            return_workshop = int(workshop_id[0])

        equip_id = None
        if self.request.GET.get('equip_id'):
            equip_id = int(self.request.GET.get('equip_id'))
            return_machine = int(equip_id)

        context = super().get_context_data(**kwargs)
        context['return_machine'] = return_machine
        context['return_workshop'] = return_workshop
        filter = StatisticsFilter(self.request.GET, queryset=ClassifiedInterval.objects.all())
        context['filter'] = filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # if end_date == '':
        #     end_date = start_date
        #     print(end_date)

        context['machines'] = Equipment.objects.filter(is_in_monitoring=True).order_by("code")
        context['workshops'] = Workshop.objects.all()
        problem_machines = [x.id for x in Equipment.objects.filter(problem_machine=True, is_in_monitoring=True)]
        if start_date is not None and start_date != '' and end_date is not None and end_date != '':

            if equip_id is not None:
                if equip_id not in problem_machines:
                    stat_data = ClassifiedInterval.get_statistics(start_date, end_date, workshop_id=workshop_id,
                                                                  equipment=equip_id)
                else:
                    pr_m = Equipment.objects.get(id=equip_id)
                    stat_data = {}
                    stat_data['total'] = {'user_stats': {'Не указано': 140},
                                          'auto_stats': {'001 - Простой': 140, '000 - Оборудование работает': 9940}}
                    stat_data[str(pr_m)] = pr_m.problem_statistics(start_date, end_date)

            else:
                stat_data = ClassifiedInterval.get_statistics(start_date, end_date, workshop_id=workshop_id,
                                                              equipment=equip_id)
                pr_machs = Equipment.objects.filter(problem_machine=True, workshop_id__in=workshop_id)
                for x in pr_machs:
                    stat_data[str(x)] = x.problem_statistics(start_date, end_date)

            context['statistics'] = prepare_data_for_google_charts_bar(stat_data)
            context['colors'] = [{'description': col['code'] + ' - ' + col['description'],
                                  'color': col['color'] if col['color'] else '#ff0000'}
                                 for col in Reason.objects.all().values('description', 'code', 'color')]
        else:
            day = datetime.date.today()
            monday = day - datetime.timedelta(days=day.weekday()) + datetime.timedelta(days=0, weeks=-1)
            sunday = monday + datetime.timedelta(days=6)
            start_date = str(monday)
            end_date = str(sunday)

            if equip_id is not None:
                if equip_id not in problem_machines:
                    stat_data = ClassifiedInterval.get_statistics(start_date, end_date, workshop_id=workshop_id,
                                                                  equipment=equip_id)
                else:
                    pr_m = Equipment.objects.get(id=equip_id)
                    stat_data = {}
                    stat_data['total'] = {'user_stats': {'Не указано': 140},
                                          'auto_stats': {'001 - Простой': 140, '000 - Оборудование работает': 9940}}
                    stat_data[str(pr_m)] = pr_m.problem_statistics(start_date, end_date)

            else:
                stat_data = ClassifiedInterval.get_statistics(start_date, end_date, workshop_id=workshop_id,
                                                              equipment=equip_id)
                pr_machs = Equipment.objects.filter(problem_machine=True, workshop_id__in=workshop_id)
                for x in pr_machs:
                    stat_data[str(x)] = x.problem_statistics(start_date, end_date)
            # print(stat_data)
            print(stat_data)
            context['statistics'] = prepare_data_for_google_charts_bar(stat_data)
            context['colors'] = [{'description': col['code'] + ' - ' + col['description'],
                                  'color': col['color'] if col['color'] else '#ff0000'}
                                 for col in Reason.objects.all().values('description', 'code', 'color')]
        # print(context['statistics'])
        return context


def html_special_chars(text):
    if (text):
        return text.replace(u"`", u'"')


def repair_equipment(request, workshop_numb, area_numb):
    equipments = Equipment.objects.filter(is_in_repair=True, workshop__workshop_number=workshop_numb,
                                          area__area_number=area_numb).order_by('-machine_or_furnace_sign', 'id')
    reasons_and_comments = {}
    work_or_not = {}
    for x in equipments:
        if x.repair_job_status == 2 and Repair_rawdata.objects.filter(machines_id=x.id,
                                                                      repair_job_status=x.repair_job_status):
            obj = \
                Repair_rawdata.objects.filter(machines_id=x.id, repair_job_status=x.repair_job_status).order_by('-id')[
                0:1:1][0]
            if obj:
                reasons_and_comments[obj.machines_id.id] = [obj.repairer_master_reason, obj.repair_comment]
        if x.is_in_monitoring:
            if x.problem_machine:
                check = Minute_interval.objects.filter(equipment_id=x.id).order_by('-id')[0:1:1][0]
                work_or_not[x.id] = 1 if check.work_check else 2
            else:
                check = ClassifiedInterval.objects.filter(equipment_id=x.id).order_by('-id')[0:1:1][0]
                work_or_not[x.id] = check.automated_classification.id
    lenght = len(equipments)
    del_result = (lenght // 10) + 1
    if (del_result > 1 and lenght % 10 > 6) or lenght == 26:
        del_result += 1
    if del_result > 7:
        del_result = 7
    if request.method == "POST":
        form = Repairform(request.POST)
        machines_id = request.POST['machines_id']
        reason_id = request.POST.get('reason_id')
        action = request.GET['action']
        if form.is_valid():
            if action != 'get_info' and action != 'get_all_info' and action != 'add_reason' and action != 'add_comment':
                Repair_rawdata1 = form.save()
            if request.is_ajax():
                message = {'equipments': 1}
                if action == 'get_info':
                    equip_info = equipments.get(id=machines_id).repair_job_status
                    message = {'equip_status': equip_info}
                    return JsonResponse(message)
                if action == 'add_reason':
                    equip = Repair_rawdata.objects.filter(machines_id_id=machines_id, repair_job_status=1).order_by(
                        '-date')[0:1:1]
                    reas = Repair_reason.objects.get(id=reason_id)
                    equip[0].repair_reason = reas
                    equip[0].save()
                    message = {'response': '1'}
                    return JsonResponse(message)
                if action == 'add_comment':
                    new_comment = request.POST.get('comment')
                    new_comment = new_comment.replace("`", "'")
                    m_reason_id = request.POST.get('mreason')
                    equip = Repair_rawdata.objects.filter(machines_id_id=machines_id, repair_job_status=2).order_by(
                        '-date')[0:1:1]
                    actual_comment = equip[0].repair_comment
                    now = datetime.datetime.now()
                    now = now.strftime("%d-%m-%Y %H:%M")
                    if new_comment:
                        if actual_comment:
                            equip[0].repair_comment = actual_comment + '\n' + now + ' ' + new_comment
                        else:
                            equip[0].repair_comment = now + ' ' + new_comment + ' '
                    if m_reason_id:
                        m_reason = Repairer_master_reason.objects.get(id=int(m_reason_id))
                        equip[0].repairer_master_reason = m_reason
                    equip[0].save()
                    message = {'response': '1', 'newmessage': '\n' + now + ' ' + new_comment}
                    return JsonResponse(message)
                if action == 'get_all_info':
                    equip_info = []
                    for x in range(0, lenght):  # Equipment.objects.values_list('id', flat=True):
                        equip_info.append([equipments[x].id, equipments.get(id=equipments[x].id).repair_job_status])
                        # equip_info.append([x,equipments.get(id = x).repair_job_status])
                    message = {'equipments': equip_info}
                    # message = {'equipments' : [1234],1234]}
                    return JsonResponse(message)
                # return JsonResponse(message)
                return JsonResponse({'test_pss': 'test_pss'})
            else:
                return redirect('post_new', workshop_numb=workshop_numb, area_numb=area_numb)
    else:
        form = Repairform()
    return render(request, 'machines/repair_area_stats.html',
                  {'equipments': equipments, 'form': form, 'lenght': lenght, 'del_result': del_result,
                   'reasons_and_comments': reasons_and_comments, 'work_or_not': work_or_not})


def all_complexes(request):
    complexes = Complex.objects.all()
    return render(request, 'machines/complex_all.html', {'complexes': complexes})


def complex_equipments(request, complex_id):
    complex_data = Equipment.objects.filter(in_complex_id=complex_id)
    context = {'complex_data': complex_data}
    context['rawdata'] = []
    for x in complex_data:
        start_time = timezone.now() - datetime.timedelta(days=1)
        end_time = timezone.now()
        graph_qs = GraphicsData.objects.filter(equipment=x.id, date__gte=start_time,
                                               date__lte=end_time).order_by('date')
        a = []
        a.extend([gd.equipment.id, str(gd.date), gd.value] for gd in graph_qs)
        context['rawdata'].extend(a)
    return render(request, 'machines/complex.html', context)


def repair_view_data(request):
    all_area = Area.objects.all()
    area_id = [x.id for x in all_area]
    all_workshops = Workshop.objects.all()
    workshop_id = [x.pk for x in all_workshops]
    return_workshop = 0
    area_url_info = ''
    if request.GET.get('area_url_info'):
        area_id = request.GET.get('area_url_info')
        area_url_info = Area.objects.get(id=area_id)

    if request.GET.get('workshop_id_param'):
        workshop_id = request.GET.get('workshop_id_param')
        return_workshop = Workshop.objects.get(pk=workshop_id).pk

    need_id = Equipment.objects.filter(is_in_repair=True, area__id__in=area_id, workshop__pk__in=workshop_id,
                                       repair_job_status=1)
    crush_equipments = []
    for x in need_id:
        a = Repair_rawdata.objects.filter(repair_job_status=1, machines_id_id=x.id).order_by('machines_id_id',
                                                                                             '-date').distinct(
            'machines_id_id')[0:1:1]
        crush_equipments.extend(a)
    need_id_rep = Equipment.objects.filter(is_in_repair=True, area__id__in=area_id, workshop__pk__in=workshop_id,
                                           repair_job_status=2)
    repair_equipments = []
    for x in need_id_rep:
        a = Repair_rawdata.objects.filter(repair_job_status=2, machines_id_id=x.id).order_by('machines_id_id',
                                                                                             '-date').distinct(
            'machines_id_id')[0:1:1]
        repair_equipments.extend(a)
    # context={'crush_equipments':crush_equipments,'repair_equipments':repair_equipments,'all_area':all_area,'area_url_info':area_url_info}
    if request.method == "POST":
        form = Repairform(request.POST)
        action = request.GET['action']
        str_id = request.POST['id']
        if form.is_valid():
            if request.is_ajax():
                if action == 'add_comment':
                    new_comment = request.POST.get('comment')
                    new_comment = new_comment.replace("`", "'")
                    m_reason_id = request.POST.get('mreason')
                    equip = Repair_rawdata.objects.get(id=str_id)
                    actual_comment = equip.repair_comment
                    now = datetime.datetime.now()
                    now = now.strftime("%d-%m-%Y %H:%M")
                    if new_comment:
                        if actual_comment:
                            equip.repair_comment = actual_comment + '\n' + now + ' ' + new_comment
                        else:
                            equip.repair_comment = now + ' ' + new_comment + ' '
                    if m_reason_id:
                        m_reason = Repairer_master_reason.objects.get(id=int(m_reason_id))
                        equip.repairer_master_reason = m_reason
                    equip.save()
                    message = {'response': '1', 'newmessage': '\n' + now + ' ' + new_comment}
                    return JsonResponse(message)
                return JsonResponse({'test_pss': 'test_pss'})
            else:
                return redirect('repair_view_data')
    else:
        form = Repairform()
    context = {'all_workshops': all_workshops, 'return_workshop': return_workshop, 'crush_equipments': crush_equipments,
               'repair_equipments': repair_equipments, 'form': form, 'all_area': all_area,
               'area_url_info': area_url_info}
    return render(request, 'machines/repair_view_data.html', context)


def repair_statistics(request):
    all_area = Area.objects.all()
    all_workshops = Workshop.objects.all()

    area_id_param = tuple(x.id for x in all_area)
    workshop_id_param = tuple(x.pk for x in all_workshops)
    return_workshop = 0
    return_area = 0
    start_interval = '2020-11-01'
    now = datetime.datetime.now().date()
    end_interval = str(now.year) + '-' + (
        str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
                       str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))
    bool_limit = (False, True)

    if request.GET.get('area_id_param'):
        if request.GET.get('area_id_param') == '0':
            area_id_param = tuple(x.id for x in all_area)
            return_area = 0
        else:
            area_id_param = request.GET.get('area_id_param'),
            return_area = area_id_param[0]
    if request.GET.get('workshop_id_param'):
        if request.GET.get('workshop_id_param') == '0':
            workshop_id_param = tuple(x.pk for x in all_workshops)
            return_workshop = 0
        else:
            workshop_id_param = request.GET.get('workshop_id_param'),
            return_workshop = workshop_id_param[0]

    if request.GET.get('start_date'):
        start_interval = request.GET.get('start_date')
        if start_interval < '2020-11-01': start_interval = '2020-11-01'
    if request.GET.get('end_date'):
        end_interval = request.GET.get('end_date')
        if end_interval > (
                str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
                str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))): end_interval = str(now.year) + '-' + (
            str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (str(now.day) if len(
            str(now.day)) >= 2 else '0' + str(now.day))
    if request.GET.get('bool_limit'):
        bool_limit = bool(request.GET.get('bool_limit')),
    # Если начало интервала меньше даты начала статистики,а конец интервала больше даты конца статистики, то считаем полную статистику по станкам
    if start_interval == '2020-11-01' and end_interval == (
            str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
            str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))):
        equip_id = Equipment.objects.filter(is_in_repair=True)
        for x in equip_id:
            if x.timetable == '8/5':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        b.end_date = None
                        b.end_time = None
                        b.de_facto = get_de_facto_time(b.start_date, datetime.datetime.now().date(), b.start_time,
                                                       datetime.datetime.now().time())
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            if a.end_date:
                                a.de_facto = get_de_facto_time(a.start_date, a.end_date, a.start_time, a.end_time)
                            else:
                                # logger.error("repair_statistics - Record is broken %d", a.equipment_id)
                                continue
                            a.save()
                    elif len(stats) == 1:
                        a = stats[0]
                        a.end_date = None
                        a.end_time = None
                        a.de_facto = get_de_facto_time(a.start_date, datetime.datetime.now().date(), a.start_time,
                                                       datetime.datetime.now().time())
                        a.save()
                else:
                    continue
            elif x.timetable == '24/7':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                now = datetime.datetime.now()
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        b.end_date = None
                        b.end_time = None
                        b.de_facto = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour,
                                                       minute=now.minute) - datetime.datetime(year=b.start_date.year,
                                                                                              month=b.start_date.month,
                                                                                              day=b.start_date.day,
                                                                                              hour=b.start_time.hour,
                                                                                              minute=b.start_time.minute)
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            if a.end_date and a.end_time:
                                a.de_facto = datetime.datetime(year=a.end_date.year, month=a.end_date.month,
                                                               day=a.end_date.day, hour=a.end_time.hour,
                                                               minute=a.end_time.minute) - datetime.datetime(
                                    year=a.start_date.year, month=a.start_date.month, day=a.start_date.day,
                                    hour=a.start_time.hour, minute=a.start_time.minute)
                            else:
                                # logger.error("repair_statistics - Record is broken %d", a.equipment_id)
                                continue
                            a.save()
                    elif len(stats) == 1:
                        b = stats[0]
                        b.end_date = None
                        b.end_time = None
                        b.de_facto = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour,
                                                       minute=now.minute) - datetime.datetime(year=b.start_date.year,
                                                                                              month=b.start_date.month,
                                                                                              day=b.start_date.day,
                                                                                              hour=b.start_time.hour,
                                                                                              minute=b.start_time.minute)
                        b.save()
                else:
                    continue

    # Если меняем фильтр старта
    elif start_interval > '2020-11-01' and end_interval == (
            str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
            str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))):
        equip_id = Equipment.objects.filter(is_in_repair=True)
        now = datetime.datetime.now()
        for x in equip_id:
            start_1 = datetime.date(year=int(start_interval[0:4:1]), month=int(start_interval[5:7:1]),
                                    day=int(start_interval[8:10:1]))
            start_1_time = datetime.time(hour=17, minute=00)
            timetable_check = Repair_statistics.objects.filter(equipment_id=x.id).order_by('id')

            if timetable_check:
                timetable_check_id = timetable_check[0]
                if timetable_check_id.start_date > start_1:
                    start_1 = timetable_check_id.start_date

            if x.timetable == '8/5':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_1,
                                                         start_date__lte=end_interval).order_by('id')
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        b.de_facto = get_de_facto_time(start_1, b.end_date, start_1_time, b.end_time)
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            a.de_facto = get_de_facto_time(a.start_date, a.end_date, a.start_time, a.end_time)
                            a.save()
                    elif len(stats) == 1:
                        b = stats[0]
                        b.de_facto = get_de_facto_time(start_1, datetime.datetime.now().date(), start_1_time,
                                                       datetime.datetime.now().time())
                        b.save()

            elif x.timetable == '24/7':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_1,
                                                         start_date__lte=end_interval).order_by('id')
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        # b.de_facto=datetime.timedelta(days=0,hours=0,minutes=0)
                        b.de_facto = datetime.datetime(year=b.end_date.year, month=b.end_date.month, day=b.end_date.day,
                                                       hour=b.end_time.hour,
                                                       minute=b.end_time.minute) - datetime.datetime(year=start_1.year,
                                                                                                     month=start_1.month,
                                                                                                     day=start_1.day,
                                                                                                     hour=start_1_time.hour,
                                                                                                     minute=start_1_time.minute)
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            a.de_facto = datetime.datetime(year=a.end_date.year, month=a.end_date.month,
                                                           day=a.end_date.day, hour=a.end_time.hour,
                                                           minute=a.end_time.minute) - datetime.datetime(
                                year=a.start_date.year, month=a.start_date.month, day=a.start_date.day,
                                hour=a.start_time.hour, minute=a.start_time.minute)
                            a.save()
                    elif len(stats) == 1:
                        b = stats[0]
                        # b.de_facto=datetime.timedelta(days=0,hours=0,minutes=0)
                        b.de_facto = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour,
                                                       minute=now.minute) - datetime.datetime(year=start_1.year,
                                                                                              month=start_1.month,
                                                                                              day=start_1.day,
                                                                                              hour=start_1_time.hour,
                                                                                              minute=start_1_time.minute)
                        b.save()
    # Если меняем дату финиша
    elif start_interval == '2020-11-01' and end_interval < (
            str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
            str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))):
        equip_id = Equipment.objects.filter(is_in_repair=True)
        now = datetime.datetime.now()
        for x in equip_id:
            end_1 = datetime.date(year=int(end_interval[0:4:1]), month=int(end_interval[5:7:1]),
                                  day=int(end_interval[8:10:1]))
            end_1_time = datetime.time(hour=23, minute=59)
            timetable_check = Repair_statistics.objects.filter(equipment_id=x.id).order_by('id')
            if timetable_check:
                timetable_check_id = timetable_check[0]
                if timetable_check_id.start_date > end_1:
                    stats = Repair_statistics.objects.filter(equipment_id=x.id)
                    for x in stats:
                        x.de_facto = datetime.timedelta(days=0, hours=0, minutes=0)
                        x.save()
                    continue

            if x.timetable == '8/5':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_interval,
                                                         start_date__lte=end_1).order_by('-id')
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        b.de_facto = get_de_facto_time(b.start_date, end_1, b.start_time, end_1_time)
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            a.de_facto = get_de_facto_time(a.start_date, a.end_date, a.start_time, a.end_time)
                            a.save()
                    elif len(stats) == 1:
                        b = stats[0]
                        b.de_facto = get_de_facto_time(b.start_date, end_1, b.start_time, end_1_time)
                        b.save()

            if x.timetable == '24/7':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_interval,
                                                         start_date__lte=end_1).order_by('-id')
                if stats:
                    if len(stats) > 1:
                        b = stats[0]
                        b.de_facto = datetime.datetime(year=end_1.year, month=end_1.month, day=end_1.day,
                                                       hour=end_1_time.hour,
                                                       minute=end_1_time.minute) - datetime.datetime(
                            year=b.start_date.year, month=b.start_date.month, day=b.start_date.day,
                            hour=b.start_time.hour, minute=b.start_time.minute)
                        b.save()
                        for y in range(1, len(stats), 1):
                            a = stats[y]
                            a.de_facto = datetime.datetime(year=a.end_date.year, month=a.end_date.month,
                                                           day=a.end_date.day, hour=a.end_time.hour,
                                                           minute=a.end_time.minute) - datetime.datetime(
                                year=a.start_date.year, month=a.start_date.month, day=a.start_date.day,
                                hour=a.start_time.hour, minute=a.start_time.minute)
                            a.save()
                    elif len(stats) == 1:
                        b = stats[0]
                        b.de_facto = datetime.datetime(year=end_1.year, month=end_1.month, day=end_1.day,
                                                       hour=end_1_time.hour,
                                                       minute=end_1_time.minute) - datetime.datetime(
                            year=b.start_date.year, month=b.start_date.month, day=b.start_date.day,
                            hour=b.start_time.hour, minute=b.start_time.minute)
                        b.save()

    # Если меняли дату старта и финиша
    elif start_interval > '2020-11-01' and end_interval < (
            str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
            str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))):
        equip_id = Equipment.objects.filter(is_in_repair=True)
        now = datetime.datetime.now()
        for x in equip_id:
            start_1 = datetime.date(year=int(start_interval[0:4:1]), month=int(start_interval[5:7:1]),
                                    day=int(start_interval[8:10:1]))
            start_1_time = datetime.time(hour=17, minute=00)
            end_1 = datetime.date(year=int(end_interval[0:4:1]), month=int(end_interval[5:7:1]),
                                  day=int(end_interval[8:10:1]))
            end_1_time = datetime.time(hour=23, minute=59)
            timetable_check = Repair_statistics.objects.filter(equipment_id=x.id).order_by('id')
            if timetable_check:
                timetable_check_id = timetable_check[0]
                if timetable_check_id.start_date > end_1:
                    stats = Repair_statistics.objects.filter(equipment_id=x.id)
                    for x in stats:
                        x.de_facto = datetime.timedelta(days=0, hours=0, minutes=0)
                        x.save()
                    continue
                if timetable_check_id.start_date > start_1:
                    start_1 = timetable_check_id.start_date

            if x.timetable == '8/5':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_1,
                                                         start_date__lte=end_1).order_by('id')
                if stats:
                    if len(stats) == 2:
                        a = stats[0]
                        b = stats[1]
                        a.de_facto = get_de_facto_time(start_1, a.end_date, start_1_time, a.end_time)
                        b.de_facto = get_de_facto_time(b.start_date, end_1, b.start_time, end_1_time)
                        a.save()
                        b.save()
                    elif len(stats) == 1:
                        a = stats[0]
                        a.de_facto = get_de_facto_time(start_1, end_1, start_1_time, end_1_time)
                        a.save()
                    elif len(stats) > 2:
                        a = stats[0]
                        b = stats.reverse()[0]
                        a.de_facto = get_de_facto_time(start_1, a.end_date, start_1_time, a.end_time)
                        b.de_facto = get_de_facto_time(b.start_date, end_1, b.start_time, end_1_time)
                        a.save()
                        b.save()
                        for y in range(1, len(stats) - 1, 1):
                            q = stats[y]
                            q.de_facto = get_de_facto_time(q.start_date, q.end_date, q.start_time, q.end_time)
                            q.save()

            if x.timetable == '24/7':
                stats = Repair_statistics.objects.filter(equipment_id=x.id).order_by('-id')
                if stats:
                    a = stats[0]
                    a.end_date = datetime.datetime.now().date()
                    a.end_time = datetime.datetime.now().time()
                    a.save()
                stats = Repair_statistics.objects.filter(equipment_id=x.id, end_date__gte=start_1,
                                                         start_date__lte=end_1).order_by('id')
                if stats:
                    if len(stats) == 2:
                        a = stats[0]
                        b = stats[1]
                        # a.de_facto=datetime.timedelta(days=0,hours=0,minutes=0)
                        a.de_facto = datetime.datetime(year=a.end_date.year, month=a.end_date.month, day=a.end_date.day,
                                                       hour=a.end_time.hour,
                                                       minute=a.end_time.minute) - datetime.datetime(year=start_1.year,
                                                                                                     month=start_1.month,
                                                                                                     day=start_1.day,
                                                                                                     hour=start_1_time.hour,
                                                                                                     minute=start_1_time.minute)
                        b.de_facto = datetime.datetime(year=end_1.year, month=end_1.month, day=end_1.day,
                                                       hour=end_1_time.hour,
                                                       minute=end_1_time.minute) - datetime.datetime(
                            year=b.start_date.year, month=b.start_date.month, day=b.start_date.day,
                            hour=b.start_time.hour, minute=b.start_time.minute)
                        # b.de_facto=datetime.timedelta(days=0,hours=0,minutes=0)
                        a.save()
                        b.save()
                    elif len(stats) == 1:
                        a = stats[0]
                        # a.de_facto=datetime.timedelta(days=0,hours=0,minutes=0)
                        a.de_facto = datetime.datetime(year=end_1.year, month=end_1.month, day=end_1.day,
                                                       hour=end_1_time.hour,
                                                       minute=end_1_time.minute) - datetime.datetime(year=start_1.year,
                                                                                                     month=start_1.month,
                                                                                                     day=start_1.day,
                                                                                                     hour=start_1_time.hour,
                                                                                                     minute=start_1_time.minute)
                        a.save()
                    elif len(stats) > 2:
                        a = stats[0]
                        b = stats.reverse()[0]
                        a.de_facto = datetime.datetime(year=a.end_date.year, month=a.end_date.month, day=a.end_date.day,
                                                       hour=a.end_time.hour,
                                                       minute=a.end_time.minute) - datetime.datetime(year=start_1.year,
                                                                                                     month=start_1.month,
                                                                                                     day=start_1.day,
                                                                                                     hour=start_1_time.hour,
                                                                                                     minute=start_1_time.minute)
                        b.de_facto = datetime.datetime(year=end_1.year, month=end_1.month, day=end_1.day,
                                                       hour=end_1_time.hour,
                                                       minute=end_1_time.minute) - datetime.datetime(
                            year=b.start_date.year, month=b.start_date.month, day=b.start_date.day,
                            hour=b.start_time.hour, minute=b.start_time.minute)
                        a.save()
                        b.save()
                        for y in range(1, len(stats) - 1, 1):
                            q = stats[y]
                            q.de_facto = datetime.datetime(year=q.end_date.year, month=q.end_date.month,
                                                           day=q.end_date.day, hour=q.end_time.hour,
                                                           minute=q.end_time.minute) - datetime.datetime(
                                year=q.start_date.year, month=q.start_date.month, day=q.start_date.day,
                                hour=q.start_time.hour, minute=q.start_time.minute)
                            q.save()

    sql_query = Repair_statistics.objects.raw('''select
                                                    1 as id,equipment_id,
                                                    coalesce(sum(case when a.repair_job_status=0 then de_facto end),'0:00:00') as work,
                                                    coalesce(sum(case when a.repair_job_status=1 then de_facto end),'0:00:00') as crush,
                                                    coalesce(sum(case when a.repair_job_status=2 then de_facto end),'0:00:00') as repair,
                                                    extract (epoch from(coalesce(sum(case when a.repair_job_status=0 then de_facto end),'0:00:00')))as ep_work,
                                                    extract (epoch from(coalesce(sum(case when a.repair_job_status=1 then de_facto end),'0:00:00'))) as ep_crush,
                                                    extract (epoch from(coalesce(sum(case when a.repair_job_status=2 then de_facto end),'0:00:00'))) as ep_repair
                                                    from machines_repair_statistics a
                                                    join machines_equipment b on a.equipment_id=b.id
                                                    where b.area_id in %(area_id_param)s
                                                    and b.workshop_id in %(workshop_id_param)s 
                                                    and b.is_limit in %(bool_limit)s
                                                    and (%(start_interval)s<=coalesce(a.end_date,current_timestamp) and %(end_interval)s>=a.start_date)
                                                    group by equipment_id 
                                                     ''', params={'area_id_param': area_id_param,
                                                                  'workshop_id_param': workshop_id_param,
                                                                  'start_interval': start_interval,
                                                                  'end_interval': end_interval,
                                                                  'bool_limit': bool_limit})
    filter = calendar_repair(0, queryset=Equipment.objects.all())  # queryset=ClassifiedInterval.objects.all())
    context = {'sql_query': sql_query, 'all_workshops': all_workshops, 'workshop_id_param': return_workshop,
               'all_area': all_area, 'filter': filter, 'area_id_param': return_area, 'start_interval': start_interval,
               'end_interval': end_interval, 'bool_limit': bool_limit[0]}

    return render(request, 'machines/repair_statistics.html', context)


def work_statistics(request):
    count_objects = len(Equipment.objects.filter(is_in_monitoring=True, machine_or_furnace_sign=True))

    old_algoritm_objects = Equipment.objects.filter(is_in_monitoring=True, machine_or_furnace_sign=True,
                                                    problem_machine=False)
    old_algoritm_id = tuple(x.id for x in old_algoritm_objects)
    new_algoritm_objects = Equipment.objects.filter(is_in_monitoring=True, machine_or_furnace_sign=True,
                                                    problem_machine=True)
    new_algoritm_id = tuple(x.id for x in new_algoritm_objects)
    return_object_id = 0
    delta_days = 15
    all_workshops = Workshop.objects.all()
    workshop_id = tuple(x.pk for x in all_workshops)
    return_workshop_id = 0

    if request.GET.get('workshop_id_param'):
        if request.GET.get('workshop_id_param') != '0':
            workshop_id = int(request.GET.get('workshop_id_param')), 0
            return_workshop_id = int(workshop_id[0])
            workshop_equipment = Equipment.objects.filter(workshop_id=request.GET.get('workshop_id_param'),
                                                          is_in_monitoring=True, machine_or_furnace_sign=True)
            count_objects = len(workshop_equipment)

    if request.GET.get('equipment_id_param'):
        if request.GET.get('equipment_id_param') != '0':
            obj = Equipment.objects.get(id=request.GET.get('equipment_id_param'))
            if obj:
                if obj.problem_machine:
                    new_algoritm_id = int(request.GET.get('equipment_id_param')), 0
                    old_algoritm_id = 0, 0
                    return_object_id = int(new_algoritm_id[0])
                    count_objects = 1
                else:
                    old_algoritm_id = int(request.GET.get('equipment_id_param')), 0
                    new_algoritm_id = 0, 0
                    return_object_id = int(old_algoritm_id[0])
                    count_objects = 1

    now = datetime.datetime.now()
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=delta_days)
    end_date = str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
        str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))
    start_date = str(start_date.year) + '-' + (
        str(start_date.month) if len(str(start_date.month)) >= 2 else '0' + str(start_date.month)) + '-' + (
                     str(start_date.day) if len(str(start_date.day)) >= 2 else '0' + str(start_date.day))
    end_1 = datetime.date(year=int(end_date[0:4:1]), month=int(end_date[5:7:1]), day=int(end_date[8:10:1]))
    start_1 = datetime.date(year=int(start_date[0:4:1]), month=int(start_date[5:7:1]), day=int(start_date[8:10:1]))
    if request.GET.get('end_date'):
        end_date = request.GET.get('end_date')
        if end_date > (
                str(now.year) + '-' + (str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
                str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))): end_date = str(now.year) + '-' + (
            str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (str(now.day) if len(
            str(now.day)) >= 2 else '0' + str(now.day))
        end_1 = datetime.date(year=int(end_date[0:4:1]), month=int(end_date[5:7:1]), day=int(end_date[8:10:1]))
    if request.GET.get('start_date'):
        start_date = request.GET.get('start_date')
        # if start_date < '2021-03-01': start_date='2021-03-01'
        start_1 = datetime.date(year=int(start_date[0:4:1]), month=int(start_date[5:7:1]), day=int(start_date[8:10:1]))

    if end_1 and start_1:
        delta_days = (end_1 - start_1).days

    graphics_data = {}

    kek = {}
    for x in range(0, delta_days + 1):
        starting = start_1 + datetime.timedelta(days=x)
        ending = start_1 + datetime.timedelta(days=x + 1)

        starting = str(starting.year) + '-' + (
            str(starting.month) if len(str(starting.month)) >= 2 else '0' + str(starting.month)) + '-' + (
                       str(starting.day) if len(str(starting.day)) >= 2 else '0' + str(starting.day))
        ending = str(ending.year) + '-' + (
            str(ending.month) if len(str(ending.month)) >= 2 else '0' + str(ending.month)) + '-' + (
                     str(ending.day) if len(str(ending.day)) >= 2 else '0' + str(ending.day))

        sql_query = ClassifiedInterval.objects.raw('''select 1 as id,%(starting)s as starting,coalesce(((EXTRACT(EPOCH FROM (
                                                                                        select sum(X.sum)from (
                                                                                                                select sum(LEAST (a.end,%(ending)s)-GREATEST (a.start,%(starting)s)),
                                                                                                                       a.equipment_id 
                                                                                                                       from machines_classifiedinterval a 
                                                                                                                       join machines_equipment b on a.equipment_id=b.id
                                                                                                                       where automated_classification_id=1 
                                                                                                                       and a.start <= %(ending)s 
                                                                                                                       AND a.end >= %(starting)s 
                                                                                                                       and equipment_id in %(old_algoritm_id)s and b.workshop_id in %(workshop_id)s
                                                                                                                       group by equipment_id
                                                                                                                union
                                                                                                                select sum(a.ending-a.starting),a.equipment_id 
                                                                                                                       from machines_hour_interval  a
                                                                                                                       join machines_equipment b on a.equipment_id=b.id 
                                                                                                                       where work_check=True 
                                                                                                                       and starting >=%(starting)s
                                                                                                                       and ending <=%(ending)s
                                                                                                                       and equipment_id in %(new_algoritm_id)s and b.workshop_id in %(workshop_id)s
                                                                                                                       group by equipment_id
                                                                                                                ) as X)
                                                                                                                )/3600)/(%(count_objects)s*24))*100,0) as percent''',
                                                   params={'ending': ending, 'starting': starting,
                                                           'old_algoritm_id': old_algoritm_id,
                                                           'new_algoritm_id': new_algoritm_id,
                                                           'count_objects': count_objects, 'workshop_id': workshop_id})

        graphics_data[x] = sql_query[0]

    equipments = Equipment.objects.filter(is_in_monitoring=True, machine_or_furnace_sign=True)
    filter = calendar_repair(0, queryset=Equipment.objects.all())
    context = {'equipments': equipments, 'all_workshops': all_workshops, 'return_workshop_id': return_workshop_id,
               'return_object_id': return_object_id, 'start_date': start_date, 'end_date': end_date,
               'graphics_data': graphics_data, 'filter': filter}

    return render(request, 'machines/work_statistics.html', context)


def repair_statistics_diagram(request):
    all_area = Area.objects.all()

    area_id_param = tuple(x.id for x in all_area)
    return_area = 0
    all_workshops = Workshop.objects.all()
    workshop_id_param = tuple(x.pk for x in all_workshops)
    return_workshop = 0
    now = datetime.datetime.now().date()
    end_interval = str(now.year) + '-' + (
        str(now.month) if len(str(now.month)) >= 2 else '0' + str(now.month)) + '-' + (
                       str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))
    start_interval = now - datetime.timedelta(days=7)
    start_interval = str(start_interval.year) + '-' + (
        str(start_interval.month) if len(str(start_interval.month)) >= 2 else '0' + str(start_interval.month)) + '-' + (
                         str(start_interval.day) if len(str(start_interval.day)) >= 2 else '0' + str(
                             start_interval.day))
    bool_limit = (False, True)

    if request.GET.get('area_id_param'):
        if request.GET.get('area_id_param') == '0':
            area_id_param = tuple(x.id for x in all_area)
            return_area = 0
        else:
            area_id_param = request.GET.get('area_id_param'),
            return_area = area_id_param[0]

    if request.GET.get('workshop_id_param'):
        if request.GET.get('workshop_id_param') == '0':
            workshop_id_param = tuple(x.pk for x in all_workshops)
            return_workshop = 0
        else:
            workshop_id_param = request.GET.get('workshop_id_param'),
            return_workshop = workshop_id_param[0]

    if request.GET.get('start_date'):
        start_interval = request.GET.get('start_date')
    if request.GET.get('end_date'):
        end_interval = request.GET.get('end_date')
    if request.GET.get('bool_limit'):
        bool_limit = bool(request.GET.get('bool_limit')),

    avg_crush = Repair_history.objects.raw('''select 1 as id,TO_CHAR(avg(repair_date-crush_date),'DD:HH24:MI') as data from machines_repair_history a 
                                              join machines_equipment b on a.equipment_id=b.id
                                              where %(start_interval)s<=a.repair_date and %(end_interval)s >=a.crush_date and b.workshop_id in %(workshop_id_param)s and b.area_id in %(area_id_param)s''',
                                           params={'start_interval': start_interval, 'end_interval': end_interval,
                                                   'workshop_id_param': workshop_id_param,
                                                   'area_id_param': area_id_param})
    avg_repair = Repair_history.objects.raw('''select 1 as id,TO_CHAR(avg(return_to_work_date-repair_date),'DD:HH24:MI') as data from machines_repair_history a 
                                                join machines_equipment b on a.equipment_id=b.id
                                                where %(start_interval)s<=a.return_to_work_date and %(end_interval)s >=a.repair_date and b.workshop_id in %(workshop_id_param)s and b.area_id in %(area_id_param)s'''
                                            , params={'start_interval': start_interval, 'end_interval': end_interval,
                                                      'workshop_id_param': workshop_id_param,
                                                      'area_id_param': area_id_param})

    if avg_crush[0].data:
        if str(avg_crush[0].data[0:2]) != '00':
            avg_crush = 'Дней: ' + str(avg_crush[0].data[0:2]) + '  Часов: ' + str(
                avg_crush[0].data[3:5]) + '  Минут: ' + str(avg_crush[0].data[6:8])
        else:
            avg_crush = 'Часов: ' + str(avg_crush[0].data[3:5]) + '  Минут: ' + str(avg_crush[0].data[6:8])


    else:
        avg_crush = 'Недостаточно данных'

    if avg_repair[0].data:
        if str(avg_repair[0].data[0:2]) != '00':
            avg_repair = 'Дней: ' + str(avg_repair[0].data[0:2]) + '  Часов: ' + str(
                avg_repair[0].data[3:5]) + '  Минут: ' + str(avg_repair[0].data[6:8])
        else:
            avg_repair = 'Часов: ' + str(avg_repair[0].data[3:5]) + '  Минут: ' + str(avg_repair[0].data[6:8])
    else:
        avg_repair = 'Недостаточно данных'

    to_service = Repair_rawdata.objects.raw('''select 1 as id,count(*) as count,machines_id_id 
                                               from machines_repair_rawdata a
                                               join machines_equipment b on a.machines_id_id=b.id
                                               where a.repair_job_status=2 and a.repairer_master_reason_id=18
                                               and  b.area_id in %(area_id_param)s  and b.is_limit in %(bool_limit)s 
                                               and b.workshop_id in %(workshop_id_param)s
                                               and a.date>=%(start_interval)s and a.date <=( date %(end_interval)s + integer '1')
                                               group by a.machines_id_id
                                               ''', params={'area_id_param': area_id_param,
                                                            'workshop_id_param': workshop_id_param,
                                                            'start_interval': start_interval,
                                                            'end_interval': end_interval, 'bool_limit': bool_limit})

    sql_all_count = Repair_rawdata.objects.raw('''select 1 as id,count(a.id) as count
                                                  from machines_repair_rawdata a
                                                  join machines_equipment b on a.machines_id_id=b.id
                                                  where a.repair_job_status=1  and  b.area_id in %(area_id_param)s and b.workshop_id in %(workshop_id_param)s and b.is_limit in %(bool_limit)s and a.date>=%(start_interval)s 
                                                  and a.date <=( date %(end_interval)s + integer '1')''',
                                               params={'area_id_param': area_id_param,
                                                       'workshop_id_param': workshop_id_param,
                                                       'start_interval': start_interval, 'end_interval': end_interval,
                                                       'bool_limit': bool_limit})[0]

    sql_crush_equipment = Repair_rawdata.objects.raw('''select 1 as id,count(*) as count,machines_id_id  from machines_repair_rawdata a
                                                     join machines_equipment b on a.machines_id_id=b.id
                                                     where a.repair_job_status=1  and  b.area_id in %(area_id_param)s and b.workshop_id in %(workshop_id_param)s and b.is_limit in %(bool_limit)s and a.date>=%(start_interval)s 
                                                     and a.date <=( date %(end_interval)s + integer '1') 
                                                     group by a.machines_id_id
                                                     ''', params={'area_id_param': area_id_param,
                                                                  'workshop_id_param': workshop_id_param,
                                                                  'start_interval': start_interval,
                                                                  'end_interval': end_interval,
                                                                  'bool_limit': bool_limit})

    sql_reason_stat = Repair_rawdata.objects.raw('''select 1 as id,count(*) as count,repairer_master_reason_id  from machines_repair_rawdata a
                                                    join machines_equipment b on a.machines_id_id=b.id
                                                    where a.repair_job_status=2 and  b.area_id in %(area_id_param)s and b.workshop_id in %(workshop_id_param)s and b.is_limit in %(bool_limit)s and a.date>=%(start_interval)s 
                                                    and a.date <=( date %(end_interval)s + integer '1')
                                                    and a.repairer_master_reason_id<>18
                                                    group by a.repairer_master_reason_id''',
                                                 params={'area_id_param': area_id_param,
                                                         'workshop_id_param': workshop_id_param,
                                                         'start_interval': start_interval, 'end_interval': end_interval,
                                                         'bool_limit': bool_limit})

    sql_max_count = Repair_rawdata.objects.raw('''select 1 as id,count(*) as count,repair_reason_id as id_id from machines_repair_rawdata a
                                                    join machines_equipment b on a.machines_id_id=b.id
                                                    where a.repair_job_status = 1
                                                    and b.area_id in %(area_id_param)s  and b.is_limit in %(bool_limit)s 
                                                    and b.workshop_id in %(workshop_id_param)s 
                                                    and a.date>=%(start_interval)s and a.date <=( date %(end_interval)s + integer '1')
                                                    and a.repair_reason_id is not null
                                                    group by repair_reason_id
                                                    order by count(*) desc limit 1''',
                                               params={'area_id_param': area_id_param,
                                                       'workshop_id_param': workshop_id_param,
                                                       'start_interval': start_interval, 'end_interval': end_interval,
                                                       'bool_limit': bool_limit})

    filter = calendar_repair(0, queryset=Equipment.objects.all())
    context = {'sql_max_count': sql_max_count, 'to_service': to_service, 'all_workshops': all_workshops,
               'workshop_id_param': return_workshop, 'all_area': all_area, 'sql_all_count': sql_all_count,
               'sql_crush_equipment': sql_crush_equipment, 'sql_reason_stat': sql_reason_stat, 'filter': filter,
               'area_id_param': return_area, 'start_interval': start_interval, 'end_interval': end_interval,
               'bool_limit': bool_limit[0], 'avg_crush': avg_crush, 'avg_repair': avg_repair}

    return render(request, 'machines/teststatnew.html', context)


def repair_history(request):
    all_area = Area.objects.all()
    area_id_param = tuple(x.id for x in all_area)
    return_area = 0
    all_repairers = Repairer.objects.all()
    repairer_id_param = tuple(x.id for x in all_repairers)
    return_repairer = 0
    start_interval = '2020-05-25'
    now = datetime.datetime.now().date()
    end_interval = str(now.year) + '-' + str(now.month) + '-' + (
        str(now.day) if len(str(now.day)) >= 2 else '0' + str(now.day))
    all_equipments = Equipment.objects.filter(is_in_repair=True)
    equipment_id_param = tuple(x.id for x in all_equipments)
    bool_limit = (False, True)

    if request.is_ajax():
        if request.GET.get('area_id_param') and request.GET.get('area_id_param') != '0':
            area_id = request.GET.get('area_id_param')
            equipments = all_equipments.get(area__id=area_id)
            message = {'equipments': equipments}
            return JsonResponse(message)
        else:
            return JsonResponse({'error': 1})
    else:
        if request.GET.get('area_id_param'):
            if request.GET.get('area_id_param') == '0':
                area_id_param = tuple(x.id for x in all_area)
                return_area = 0
            else:
                area_id_param = request.GET.get('area_id_param'),
                return_area = area_id_param[0]
        if request.GET.get('start_date'):
            start_interval = request.GET.get('start_date')
        if request.GET.get('end_date'):
            end_interval = request.GET.get('end_date')
        if request.GET.get('bool_limit') == "True":
            bool_limit = bool(request.GET.get('bool_limit')),
        if request.GET.get('repairer_id_param'):
            if request.GET.get('repairer_id_param') == '0':
                repairer_id_param = tuple(x.id for x in all_repairers)
                return_repairer = 0
            else:
                repairer_id_param = request.GET.get('repairer_id_param'),
                return_repairer = repairer_id_param[0]
        if request.GET.get('equipment_id_param'):
            equipment_id_param = request.GET.get('equipment_id_param'),
        sql_query = list(Repair_history.objects.raw('''select 1 as id,b.area_id,a.equipment_id,crush_date,repair_date,return_to_work_date,repairer_id,first_reason_id,master_reason_id,repair_comment
                                                        from machines_repair_history a
                                                        join machines_equipment b on a.equipment_id=b.id
                                                        where return_to_work_date is not null
                                                        and b.area_id in %(area_id_param)s 
                                                        and b.id in %(equipment_id_param)s
                                                        and a.repairer_id in %(repairer_id_param)s
                                                        and b.is_limit in %(bool_limit)s
                                                        and a.crush_date >=%(start_interval)s
                                                        and a.return_to_work_date <=( date %(end_interval)s + integer '1')
                                                        order by a.id desc''', params={'area_id_param': area_id_param,
                                                                                       'start_interval': start_interval,
                                                                                       'end_interval': end_interval,
                                                                                       'bool_limit': bool_limit,
                                                                                       'bool_limit': bool_limit,
                                                                                       'repairer_id_param': repairer_id_param,
                                                                                       'equipment_id_param': equipment_id_param}))

        # Пагинация
        paginator = EllipsisPaginator(sql_query, 25)
        current_page = request.GET.get('page', 1)
        page_obj = paginator.get_page(current_page)
        ellipsis_paginator = paginator.get_elided_page_range(number=current_page, on_each_side=2, on_ends=2)

        filter = calendar_repair(0, queryset=Equipment.objects.all())

        context = {'all_area': all_area, 'all_repairers': all_repairers, 'all_equipments': all_equipments,
                   'sql_query': page_obj, 'paginator': ellipsis_paginator, 'current_page': int(current_page),
                   'filter': filter,
                   'repairer_id_param': return_repairer, 'area_id_param': return_area,
                   'equipment_id_param': equipment_id_param[0], 'start_interval': start_interval,
                   'end_interval': end_interval, 'bool_limit': bool_limit[0]}
        return render(request, 'machines/repair_history.html', context)


def main_repairer(request):
    context = {'a': 123}
    return render(request, 'machines/main_repairer.html', context)


def oee(request):
    need_objects = Equipment.objects.filter(id__in=[4, 5])
    ferrarri_details, ferrarri_brak = 166, 7
    okuma_details, okuma_brak = 159, 6

    ferrarri_time = int(ClassifiedInterval.objects.raw("""select 1 as id, EXTRACT(epoch FROM sum("end"-"start")/3600) as time from machines_classifiedinterval
            where equipment_id = 4 and automated_classification_id = 1
            and "start" <='2021-07-01' and "end" >='2021-06-01'""")[0].time)

    okuma_time = int(ClassifiedInterval.objects.raw("""select 1 as id, EXTRACT(epoch FROM sum("end"-"start")/3600) as time from machines_classifiedinterval
            where equipment_id = 5 and automated_classification_id = 1
            and "start" <='2021-07-01' and "end" >='2021-06-01'""")[0].time)

    ferrari_A = ferrarri_time / 720

    ferrari_P = ferrarri_details / (2.5 * ferrarri_time)

    ferrari_Q = (ferrarri_details - ferrarri_brak) / ferrarri_details

    ferrari_OEE = ferrari_A * ferrari_P * ferrari_Q * 100

    okuma_A = okuma_time / 720

    okuma_P = okuma_details / (2.5 * okuma_time)

    okuma_Q = (okuma_details - okuma_brak) / okuma_details

    okuma_OEE = okuma_A * okuma_P * okuma_Q * 100

    return render(request, 'machines/oee.html',
                  {'ferrari_A': ferrari_A * 100, 'ferrari_P': ferrari_P * 100, 'ferrari_Q': ferrari_Q * 100,
                   'ferrari_OEE': ferrari_OEE, 'okuma_A': okuma_A * 100, 'okuma_P': okuma_P * 100,
                   'okuma_Q': okuma_Q * 100, 'okuma_OEE': okuma_OEE})


def stats_report(request):
    context = {}

    today = datetime.datetime.now()
    start_delta = datetime.timedelta(days=datetime.datetime.today().weekday(), weeks=1)

    if request.GET.get('start_date') and request.GET.get('end_date'):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
    else:
        start_date = (today - start_delta).strftime("%Y-%m-%d")
        end_date = (today - start_delta + datetime.timedelta(days=6)).strftime("%Y-%m-%d")

    return_workshop = 0
    workshop_id = [x.workshop_number for x in Workshop.objects.all()]

    if request.GET.get('workshop_id'):
        workshop_id = request.GET.get('workshop_id'),
        return_workshop = int(workshop_id[0])

    context['return_workshop'] = return_workshop

    context['filter'] = ReportFilter(request.GET, queryset=ClassifiedInterval.objects.all())

    context['date'] = {
        'start_date': dateparse.parse_date(start_date),
        'end_date': dateparse.parse_date(end_date)
    }

    # Days range for table
    day_range = []
    delta = dateparse.parse_date(end_date) - dateparse.parse_date(start_date)
    for i in range(delta.days + 1):
        day_range.append((dateparse.parse_date(start_date) + datetime.timedelta(days=i)).strftime("%A - %d.%m.%Y"))
    context['day_list'] = day_range

    context['workshops'] = Workshop.objects.all()

    # Get data from old and new statistics
    stat_data = {}
    problem_stat_data = {}

    problem_machines = [x.id for x in Equipment.objects.filter(problem_machine=True, is_in_monitoring=True,
                                                               workshop_id__in=workshop_id)]

    if start_date is not None and start_date != '' and end_date is not None and end_date != '':
        stat_data = ClassifiedInterval.get_report_data(start_date, end_date, workshop_id=workshop_id)

        problem_stat_data = Equipment.report_problem_statistics(start_date, end_date, workshop_id=workshop_id,
                                                                equipment=problem_machines)

    joined_report = stat_data['day_stats'] + problem_stat_data['day_stats']

    # Delete test machines
    for i in range(len(joined_report)):
        if joined_report[i]['code'] == "TEST":
            del joined_report[i]
            break

    total_keys_list = {**problem_stat_data['total_workshop_user_data'], **stat_data['total_workshop_user_data']}

    model_sort_joined_report = sorted(joined_report, key=lambda k: (k['model'], k['code']))

    dict_to_sorting = {
        7: 1,
        8: 2,
        26: 3,
        14: 4,
        9: 5,
        20: 6,
        1: 7
    }

    workshop_sort_joined_report = sorted(model_sort_joined_report, key=lambda k: dict_to_sorting[k['workshop_id']])

    # Merge identical reason
    if stat_data and problem_stat_data:
        for key, value in total_keys_list.items():
            t_dict = {}

            if key in stat_data['total_workshop_user_data'] and key in problem_stat_data[
                'total_workshop_user_data'] and bool(problem_stat_data['total_workshop_user_data'][key]) and bool(
                    stat_data['total_workshop_user_data'][key]):
                total_keys_list[key] = [value, problem_stat_data['total_workshop_user_data'][key]]
                for item in total_keys_list[key]:
                    for item_key, item_value in item.items():
                        if item_key in t_dict:
                            t_dict[item_key] += item_value
                        else:
                            t_dict[item_key] = item_value
                    total_keys_list[key] = t_dict
            else:
                total_keys_list[key] = value

    total_user_stats = {}

    # Calculation percent for reasons
    for workshop, reason in total_keys_list.items():
        workshop_user_stats = {}
        user_stats_value = [sum(reason.values())]
        for k, v in reason.items():
            if v == 0:
                continue
            else:
                workshop_user_stats[k] = round(v / max(user_stats_value) * 100, 1)
        total_user_stats[workshop] = sorted(workshop_user_stats.items(), key=lambda x: x[1], reverse=True)

    context['statistics'] = {
        'day_stats': workshop_sort_joined_report,
        'total_workshop_user_data': total_user_stats
    }

    # Total workshop percent
    total_workshop_percent_dict = {}

    for workshop in workshop_id:
        total_workshop_percent = 0
        total_workshop_count = 0
        for item in workshop_sort_joined_report:
            if int(item['workshop_id']) == int(workshop):
                total_workshop_percent += item['total_percent']
                total_workshop_count += 1
        if total_workshop_percent == 0:
            total_workshop_percent_dict[workshop] = 0
        else:
            total_workshop_percent_dict[workshop] = round(total_workshop_percent / total_workshop_count, 1)

    context['total_workshop_percent'] = total_workshop_percent_dict

    # Total period percents
    days_total_percent = []
    item_period_percent = []
    total_period_percent = ''
    if workshop_sort_joined_report:
        for day_count, i in enumerate(range(delta.days + 1)):
            day_total_percent = []
            for value in workshop_sort_joined_report:
                day_total_percent.append(value["days_percent"][day_count])
            days_total_percent.append(round(mean(day_total_percent), 1))
        for item in workshop_sort_joined_report:
            item_period_percent.append(item["total_percent"])
        total_period_percent = round(mean(item_period_percent), 1)
    else:
        days_total_percent = [0, 0]

    context['period_percents'] = {
        'days_total_percent': days_total_percent,
        'total_period_percent': total_period_percent
    }

    context['previous_week_data'] = get_previous_week_report(start_date, end_date)

    return render(request, 'machines/stats_report.html', context)
