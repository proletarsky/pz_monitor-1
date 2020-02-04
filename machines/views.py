# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.forms import fields
from django.forms.models import inlineformset_factory
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render
from django.urls.base import reverse_lazy
from django.utils.dateparse import parse_datetime, parse_date
from django.http import Http404
from django.http.response import HttpResponse
from django.core.paginator import Paginator
from django.views.generic import ListView, View
from django.views.generic import DetailView, UpdateView
from .models import Equipment, RawData, Reason, ClassifiedInterval, GraphicsData
from .serializers import RawDataSerializer
from .forms import ReasonForm, ClassifiedIntervalFormSet, EquipmentDetailForm
from rest_framework import viewsets, permissions, status, authentication
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .parsers import CoordinatorDataParser
from .filters import EquipmentFilter, ClassifiedIntervalFilter, StatisticsFilter
from django.utils import timezone
import re, datetime
from .helpers import prepare_data_for_google_charts_bar, get_ci_data_timeline
from qsstats import QuerySetStats
from django.db.models import Avg
from .forms import UserRegistrationForm


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
        context['filter'] = EquipmentFilter(self.request.GET, queryset=self.get_queryset())
        context['graph_data'] = get_ci_data_timeline()
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
            start_time = timezone.now() - datetime.timedelta(days=1)
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

        if self.request.POST:
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


class ClassifiedIntervalsListView(ListView):
    model = ClassifiedInterval
    # paginate_by = 20
    template_name = 'machines/classifiedintervals_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        ci_filter = ClassifiedIntervalFilter(self.request.GET,
            queryset=ClassifiedInterval.objects.filter(automated_classification__is_working=False).order_by('start'))
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
        context = super().get_context_data(**kwargs)
        filter = StatisticsFilter(self.request.GET, queryset=ClassifiedInterval.objects.all())
        context['filter'] = filter
        start_date = self.request.GET.get('start_date');
        end_date = self.request.GET.get('end_date');
        if start_date is not None and end_date is not None:
            context['statistics'] = prepare_data_for_google_charts_bar(ClassifiedInterval.get_statistics(start_date, end_date))
            context['colors'] = [{'description': col['code']+' - '+col['description'], 'color': col['color'] if col['color'] else '#ff0000'}
                                 for col in Reason.objects.all().values('description','code', 'color')]

        return context
