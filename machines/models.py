# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from statistics import mean

from machines.time_helpers import CurrentDayType, get_duration_minutes

from django.db import models
from django.db.models import Count, Max
from django.contrib.auth.models import User, Group
from django.utils import timezone, dateparse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ValidationError
import datetime
import pytz
from collections import Counter


# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование предприятия')
    group = models.ForeignKey(Group, verbose_name='Группа пользователей', on_delete=models.SET_NULL, null=True,
                              blank=True)

    def __str__(self):
        return self.name


class Coordinator(models.Model):
    name = models.CharField(max_length=50, verbose_name='Наименование', null=True, blank=True)
    mac = models.CharField(max_length=50, verbose_name='MAC координатора', null=True, blank=True)
    ip = models.CharField(max_length=50, verbose_name='ip координатора', null=True, blank=True)
    company = models.ForeignKey(Company, verbose_name='Предприятие', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name + ' ' + self.mac + ' ' + self.ip


class Reason(models.Model):
    code = models.CharField(max_length=10, verbose_name='Код')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    is_working = models.BooleanField(verbose_name='Работа', default=False)
    is_operator = models.BooleanField(verbose_name='Указывается оператором', default=False)
    selectable = models.BooleanField(verbose_name='Активность', default=False)
    color = models.CharField(max_length=7, verbose_name='Цвет в диаграммах', null=True)

    def __str__(self):
        return ('{0} - {1}'.format(self.code, self.description))


class Participant(models.Model):
    ROLE_CHOICES = (
        ('administrator', u'Администратор'),
        ('operator', u'Рабочий'),
        ('master', u'Мастер'),
        ('manager', u'Руководитель'),
    )
    surname = models.CharField(max_length=30, verbose_name='Фамилия')
    first_name = models.CharField(max_length=30, verbose_name='Имя')
    second_name = models.CharField(max_length=30, verbose_name='Отчество')
    login = models.CharField(max_length=30, verbose_name='Логин')
    phone = models.CharField(max_length=10, verbose_name='Телефон')
    role = models.CharField(max_length=20, verbose_name='Роль', choices=ROLE_CHOICES)

    def __str__(self):
        string = '{0} {1} {2}, {3}'.format(self.surname, self.first_name, self.second_name, self.role)
        return string


class RawData(models.Model):
    date = models.DateTimeField(auto_now=True)
    mac_address = models.CharField(max_length=25)
    channel = models.CharField(max_length=5, null=True)
    value = models.FloatField()
    ip = models.CharField(max_length=20, null=True)


class TimetableDetail(models.Model):
    DAYS_OF_WEEK = (
        ('Пн', 'Понедельник'),
        ('Вт', 'Вторник'),
        ('Ср', 'Среда'),
        ('Чт', 'Четверг'),
        ('Пт', 'Пятница'),
        ('Сб', 'Суббота'),
        ('Вс', 'Воскресенье')
    )
    day_of_week_start = models.CharField(max_length=14, verbose_name='С дня недели', choices=DAYS_OF_WEEK)
    day_of_week_end = models.CharField(max_length=14, verbose_name='По день недели', choices=DAYS_OF_WEEK)
    start_time1 = models.TimeField(verbose_name='Начало 1 смены', auto_now=False)
    end_time1 = models.TimeField(verbose_name='Окончание 1 смены', auto_now=False)
    lunch_start1 = models.TimeField(verbose_name='Начало обеда 1 смены', auto_now=False, null=True, blank=True)
    lunch_end1 = models.TimeField(verbose_name='Окончание обеда 1 смены', auto_now=False, null=True, blank=True)
    start_time2 = models.TimeField(verbose_name='Начало 2 смены', auto_now=False, null=True, blank=True)
    end_time2 = models.TimeField(verbose_name='Окончание 2 смены', auto_now=False, null=True, blank=True)
    lunch_start2 = models.TimeField(verbose_name='Начало обеда 2 смены', auto_now=False, null=True, blank=True)
    lunch_end2 = models.TimeField(verbose_name='Окончание обеда 2 смены', auto_now=False, null=True, blank=True)
    start_time3 = models.TimeField(verbose_name='Начало 3 смены', auto_now=False, null=True, blank=True)
    end_time3 = models.TimeField(verbose_name='Окончание 3 смены', auto_now=False, null=True, blank=True)
    lunch_start3 = models.TimeField(verbose_name='Начало обеда 3 смены', auto_now=False, null=True, blank=True)
    lunch_end3 = models.TimeField(verbose_name='Окончание обеда 3 смены', auto_now=False, null=True, blank=True)

    def clean(self):
        if (self.start_time2 is None) != (self.end_time2 is None):
            raise ValidationError('У второй смены должны быть указаны и начало и конец')
        if self.start_time2 is None and self.start_time3 is not None:
            raise ValidationError('Нельзя включить третью смену без второй')
        if (self.start_time3 is None) != (self.end_time3 is None):
            raise ValidationError('У третьей смены должны быть указаны и начало и конец')
        if (self.lunch_start1 is None) != (self.lunch_end1 is None):
            raise ValidationError('У обеда 1 смены должны быть указаны и начало и конец')
        if (self.lunch_start2 is None) != (self.lunch_end2 is None):
            raise ValidationError('У обеда 2 смены должны быть указаны и начало и конец')
        if (self.lunch_start3 is None) != (self.lunch_end3 is None):
            raise ValidationError('У обеда 3 смены должны быть указаны и начало и конец')
        if self.lunch_start1 is not None and get_duration_minutes(self.start_time1, self.lunch_start1) > 480:
            raise ValidationError('Обед 1-й смены не должен начинаться раньше начала смены')
        if self.lunch_start2 is not None and get_duration_minutes(self.start_time2, self.lunch_start2) > 480:
            raise ValidationError('Обед 1-й смены не должен начинаться раньше начала смены')
        if self.lunch_start3 is not None and get_duration_minutes(self.start_time3, self.lunch_start3) > 480:
            raise ValidationError('Обед 1-й смены не должен начинаться раньше начала смены')
        if self.lunch_end1 is not None and get_duration_minutes(self.lunch_end1, self.end_time1) > 480:
            raise ValidationError('Обед 1-й смены не должен кончаться после окончания смены')
        if self.lunch_end2 is not None and get_duration_minutes(self.lunch_end2, self.end_time2) > 480:
            raise ValidationError('Обед 2-й смены не должен кончаться после окончания смены')
        if self.lunch_end3 is not None and get_duration_minutes(self.lunch_end3, self.end_time3) > 480:
            raise ValidationError('Обед 3-й смены не должен кончаться после окончания смены')

    def __str__(self):
        if self.start_time2 is None:
            return ('{0}-{1}:(1-я смена:{2}-{3})'.format(self.day_of_week_start, self.day_of_week_end,
                                                         self.start_time1.strftime('%H:%M'),
                                                         self.end_time1.strftime('%H:%M')))
        elif self.start_time3 is None:
            return ('{0}-{1}:(1-я смена:{2}-{3}, 2-я смена:{4}-{5})'.format(self.day_of_week_start,
                                                                            self.day_of_week_end,
                                                                            self.start_time1.strftime('%H:%M'),
                                                                            self.end_time1.strftime('%H:%M'),
                                                                            self.start_time2.strftime('%H:%M'),
                                                                            self.end_time2.strftime('%H:%M')))
        else:
            return ('{0}-{1}:(1-я смена:{2}-{3}, 2-я смена:{4}-{5}), 3-я смена:{6}-{7}'
                    .format(self.day_of_week_start, self.day_of_week_end,
                            self.start_time1.strftime('%H:%M'), self.end_time1.strftime('%H:%M'),
                            self.start_time2.strftime('%H:%M'), self.end_time2.strftime('%H:%M'),
                            self.start_time3.strftime('%H:%M'), self.end_time3.strftime('%H:%M')))


class Timetable(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название расписания:')
    pre_holiday_short = models.BooleanField(verbose_name='В предпразничные дни на смены час короче',
                                            auto_created=True)

    def __str__(self):
        return self.name

    def get_current_working_intervals(self):
        todayType = CurrentDayType.get_day_type()
        short_day_of_week = [d[0] for d in TimetableDetail.DAYS_OF_WEEK]
        if todayType == 1:
            return []
        elif todayType == 0 or todayType == 2:  # common working day or eve holiday
            # to find suitable timetable detail
            todayWorkDay = timezone.localtime()
            weekDay = todayWorkDay.weekday() if CurrentDayType.get_working_day(todayWorkDay) == todayWorkDay.day \
                else (todayWorkDay - datetime.timedelta(days=1)).weekday()
            foundTD = None
            for tc in self.timetable.all():
                day_start = -1
                day_end = -1
                td = tc.details
                try:
                    day_start = short_day_of_week.index(td.day_of_week_start)
                    day_end = short_day_of_week.index(td.day_of_week_end)
                except:
                    pass
                if day_start <= weekDay <= day_end:
                    foundTD = td
                    break
            time_intervals = []
            if foundTD is None:
                return []
            else:
                sub_hour = 1 if todayType == 2 else 0
                if foundTD.lunch_start1 is None:
                    time_intervals = [(foundTD.start_time1, datetime.time(foundTD.end_time1.hour - sub_hour,
                                                                          foundTD.end_time1.minute, 0))]
                else:
                    time_intervals = [(foundTD.start_time1, foundTD.lunch_start1),
                                      (foundTD.lunch_end1, datetime.time(foundTD.end_time1.hour - sub_hour,
                                                                         foundTD.end_time1.minute, 0))]
                if foundTD.start_time2:
                    if foundTD.lunch_start2 is None:
                        time_intervals += [(foundTD.start_time2, datetime.time(foundTD.end_time2.hour - sub_hour,
                                                                               foundTD.end_time2.minute, 0))]
                    else:
                        time_intervals += [(foundTD.start_time2, foundTD.lunch_start2),
                                           (foundTD.lunch_end2, datetime.time(foundTD.end_time2.hour - sub_hour,
                                                                              foundTD.end_time2.minute, 0))]
                if foundTD.start_time3:
                    if foundTD.lunch_start3 is None:
                        time_intervals += [(foundTD.start_time3, datetime.time(foundTD.end_time3.hour - sub_hour,
                                                                               foundTD.end_time3.minute, 0))]
                    else:
                        time_intervals += [(foundTD.start_time3, foundTD.lunch_start3),
                                           (foundTD.lunch_end3, datetime.time(foundTD.end_time3.hour - sub_hour,
                                                                              foundTD.end_time3.minute, 0))]
            return time_intervals
        else:
            return []


class TimetableContent(models.Model):
    timetable = models.ForeignKey(Timetable, related_name='timetable', verbose_name='Расписание',
                                  on_delete=models.DO_NOTHING)
    details = models.ForeignKey(TimetableDetail, related_name='detail', verbose_name='Детали',
                                on_delete=models.DO_NOTHING)


# 12.08.2020 Шабанов добавление новых моделей
class Workshop(models.Model):
    workshop_number = models.IntegerField(verbose_name='Номер цеха', primary_key=True)
    name = models.CharField(max_length=50, verbose_name='Наименование')
    foreman = models.CharField(max_length=50, verbose_name='Начальник цеха', null=True, blank=True)
    company = models.ForeignKey(Company, verbose_name='Предприятие', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.workshop_number)


class Area(models.Model):
    workshop = models.ForeignKey(Workshop, verbose_name='Цех', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=50, verbose_name='Наименование')
    area_number = models.IntegerField(verbose_name='Номер участка', null=True, blank=True)
    mac_scan = models.CharField(max_length=70, verbose_name='MAC считывателя участка', blank=True, null=True)
    green_card_id = models.CharField(max_length=70, verbose_name='ID зеленой карточки')
    add_green_card_id = models.CharField(max_length=70, verbose_name='ID дополнительной зеленой карточки', blank=True,
                                         null=True)
    company = models.ForeignKey(Company, verbose_name='Предприятие', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name + ' цеха №' + str(self.workshop.workshop_number)


class Complex(models.Model):
    name = models.CharField(max_length=70, verbose_name='Наименование')
    descr = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name


class Equipment(models.Model):
    TIMETABLE_CHOICES = (
        ('8/5', '8 часов с выходными'),
        ('24/7', 'круглосуточно без выходных'),
    )
    AVAILABLE_MACS = lambda: [(m.mac_address, m.mac_address)
                              for m in RawData.objects.all().distinct('mac_address')]
    AVAILABLE_CHANNELS = lambda: [(m.channel, m.channel)
                                  for m in RawData.objects.filter(date__gte=timezone.localdate()).distinct('channel')]
    # Шабанов изменение структуры модели - поле "Цех" больше не является строкой, здесь теперь хранятся ссылки на объекты типа цех из таблицы Workshop
    workshop = models.ForeignKey(Workshop, verbose_name='Цех', on_delete=models.PROTECT, blank=True, null=True)
    # workshop=models.IntegerField(verbose_name='Цех')
    area = models.ForeignKey(Area, verbose_name='Участок', on_delete=models.PROTECT, null=True, blank=True)
    code = models.CharField(max_length=10, verbose_name='Инвентарный номер')
    model = models.CharField(max_length=20, verbose_name='Модель')
    image = models.ImageField(blank=True, upload_to='machines', verbose_name='Фото оборудования')
    description = models.TextField(max_length=1000, verbose_name='Описание', null=True, blank=True)
    timetable = models.CharField(max_length=30, verbose_name='Расписание', choices=TIMETABLE_CHOICES)
    master = models.ForeignKey(Participant, on_delete=models.PROTECT)
    machine_or_furnace_sign = models.BooleanField(verbose_name='Оборудование является станком', default=True)
    xbee_mac = models.CharField(max_length=25, verbose_name='MAC модема',
                                # choices=AVAILABLE_MACS(), -- замена выпадающего списка на текстовое поле
                                null=True, blank=True)
    main_channel = models.CharField(max_length=5, verbose_name='Канал', choices=AVAILABLE_CHANNELS(),
                                    null=True, blank=True)
    idle_threshold = models.IntegerField(verbose_name='Порог включения', default=100)
    no_load_threshold = models.FloatField(verbose_name='Порог холостого хода')
    allowed_idle_interval = models.IntegerField(verbose_name='Допустимый простой, мин', default=15)
    schedule = models.ForeignKey(Timetable, related_name='schedule', verbose_name='Режим работы',
                                 on_delete=models.DO_NOTHING, null=True)
    is_in_monitoring = models.BooleanField(verbose_name='В системе мониторинга', default=False)
    is_in_repair = models.BooleanField(verbose_name='В системе учета ремонтных работ', default=False)
    JOB_STATUSES = (
        (0, 'В рабочем состоянии'),
        (1, 'Сломан, необходим ремонт'),
        (2, 'В ремонте'),
    )
    repair_job_status = models.IntegerField(verbose_name='Статус оборудования', choices=JOB_STATUSES, null=False,
                                            default=2)
    red_card_id = models.CharField(max_length=70, verbose_name='ID красной карточки', default=1000000000)
    in_complex = models.ForeignKey(Complex, verbose_name='Входит в комплекс', on_delete=models.DO_NOTHING, null=True,
                                   blank=True)
    is_limit = models.BooleanField(verbose_name='Является лимитированным оборудованием', default=False, blank=True,
                                   null=True)
    is_cnc = models.BooleanField(verbose_name='Является станком ЧПУ', default=False)
    problem_machine = models.BooleanField(verbose_name='Новый алгоритм измерения простоев', default=False, blank=True,
                                          null=True)
    dimension_delta = models.FloatField(verbose_name='Дельта для измерения простоя', blank=True, null=True)
    coordinator = models.ForeignKey(Coordinator, verbose_name='Координатор', blank=True, null=True,
                                    on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, verbose_name='Предприятие', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.area is None:
            return '{0} - {1}, цех {2}'.format(self.code, self.model, self.workshop)
        else:
            return '{0} - {1}, {2}'.format(self.code, self.model, self.area)

    def problem_statistics(self, start, end):

        if not self.problem_machine:
            return None

        else:
            ending_ = datetime.datetime(year=int(end[0:4:1]), month=int(end[5:7:1]), day=int(end[8:10:1]), hour=0,
                                        minute=0, tzinfo=pytz.UTC)
            starting_ = datetime.datetime(year=int(start[0:4:1]), month=int(start[5:7:1]), day=int(start[8:10:1]),
                                          hour=0, minute=0, tzinfo=pytz.UTC)

            result = {}
            hour_intervals = Hour_interval.objects.filter(equipment_id=self.id, ending__gte=starting_,
                                                          starting__lte=ending_ + datetime.timedelta(days=1)).order_by('id')
            total_work = 0
            total_loss = 0
            user_reason = []
            for x in hour_intervals:
                if x.work_check:
                    total_work += 1
                else:
                    total_loss += 1
                    user_reason.append(x.user_reason)
            counter = dict(Counter(user_reason))
            user_stats = {}
            for x in counter:
                if x:
                    user_stats[str(x)] = counter[x]
                else:
                    user_stats['Не указано'] = counter[x]
            result['auto_stats'] = {'000 - Оборудование работает': total_work, '001 - Простой': total_loss}
            result['user_stats'] = user_stats
            return (result)


    @staticmethod
    def report_problem_statistics(start, end, workshop_id, equipment):
        statistics = {}

        ending = datetime.datetime(year=int(end[0:4:1]), month=int(end[5:7:1]), day=int(end[8:10:1]), hour=0,
                                    minute=0, tzinfo=pytz.UTC)
        starting = datetime.datetime(year=int(start[0:4:1]), month=int(start[5:7:1]), day=int(start[8:10:1]),
                                      hour=0, minute=0, tzinfo=pytz.UTC)

        days_stats = []
        delta = ending - starting

        for eid in equipment:
            intervals_data = []
            hour_intervals = Hour_interval.objects.filter(equipment_id=eid, ending__gte=starting,
                                                          starting__lte=ending + datetime.timedelta(days=1)).order_by('id')

            user_reason = []
            for x in hour_intervals:
                if x.work_check:
                    continue
                else:
                    user_reason.append(x.user_reason)
            counter = dict(Counter(user_reason))
            user_stats = {}
            for x in counter:
                if x:
                    user_stats[str(x)] = counter[x]
                else:
                    user_stats['000 - Не указано'] = counter[x]

            user_stats_value = [sum(user_stats.values())]
            for k, v in user_stats.items():
                if v == 0:
                    continue
                else:
                    user_stats[k] = round(v / max(user_stats_value) * 100, 1)

            for day_count, i in enumerate(range(delta.days + 1)):
                hour_intervals = Hour_interval.objects.filter(equipment_id=eid, ending__gte=starting + datetime.timedelta(days=i),
                                                              starting__lte=starting + datetime.timedelta(days=i + 1)).order_by('id')
                total_work = 0
                total_loss = 0
                for x in hour_intervals:
                    if x.work_check:
                        total_work += 1
                    else:
                        total_loss += 1
                if total_work != 0 and total_loss != 0:
                    intervals_data.append(round(100 - total_loss / (total_work + total_loss) * 100, 1))
                elif total_work == 0:
                    intervals_data.append(0)
                elif total_loss == 0:
                    intervals_data.append(100)

            sort_user_stats = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)

            days_stats.append({
                'workshop_id': Equipment.objects.filter(id=eid).values_list('workshop_id', flat=True).first(),
                'code': Equipment.objects.filter(id=eid).values_list('code', flat=True).first(),
                'model': Equipment.objects.filter(id=eid).values_list('model', flat=True).first(),
                'days_percent': intervals_data,
                'total_percent': round(mean(intervals_data), 1),
                'user_stats': sort_user_stats
            })

        total_workshop_percent_dict = {}

        total_workshop_user_data = {}

        all_workshop_id = [x.workshop_number for x in Workshop.objects.all()]

        for workshop in all_workshop_id:
            total_workshop_percent = 0
            total_workshop_count = 0
            # Total percent for period
            for item in days_stats:
                if item['workshop_id'] == workshop:
                    total_workshop_percent += item['total_percent']
                    total_workshop_count += 1
            if total_workshop_percent == 0:
                total_workshop_percent_dict[workshop] = 0
            else:
                total_workshop_percent_dict[workshop] = round(total_workshop_percent / total_workshop_count, 1)

            total_user_stats = {}

            all_problem_equipment = [x.id for x in Equipment.objects.filter(problem_machine=True, is_in_monitoring=True, workshop_id=workshop)]

            for eid in all_problem_equipment:
                hour_intervals = Hour_interval.objects.filter(equipment_id=eid, ending__gte=starting,
                                                              starting__lte=ending + datetime.timedelta(days=1)).order_by('id')
                user_reason = []
                for x in hour_intervals:
                    if x.work_check:
                        continue
                    else:
                        user_reason.append(x.user_reason)
                counter = dict(Counter(user_reason))

                for x in counter:

                    if x:
                        total_user_stats[str(x)] = counter[x]
                    else:
                        total_user_stats['000 - Не указано'] = counter[x]

            total_workshop_user_data[workshop] = total_user_stats

        statistics['day_stats'] = days_stats
        statistics['total_workshop_user_data'] = total_workshop_user_data
        return statistics


class Minute_interval(models.Model):
    starting = models.DateTimeField(verbose_name='Начало промежутка', blank=True, null=True)
    ending = models.DateTimeField(verbose_name='Конец промежутка', blank=True, null=True)
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE, null=True,
                                  blank=True)
    work_check = models.BooleanField(verbose_name='Оборудование работает?', null=True, blank=True)
    hour = models.ForeignKey('Hour_interval', verbose_name='Промежуток входит в часовой интервал', null=True,
                             blank=True, on_delete=models.CASCADE)


class Hour_interval(models.Model):
    starting = models.DateTimeField(verbose_name='Начало промежутка', blank=True, null=True)
    ending = models.DateTimeField(verbose_name='Конец промежутка', blank=True, null=True)
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE, null=True,
                                  blank=True)
    work_check = models.BooleanField(verbose_name='Оборудование работает?', null=True, blank=True)
    user_reason = models.ForeignKey(Reason, verbose_name='Причина оператора', on_delete=models.SET_NULL, null=True,
                                    blank=True, limit_choices_to={'is_operator': True})
    trinity = models.ForeignKey('Trinity_interval', verbose_name='Промежуток входит в 3-часовой интервал', null=True,
                                blank=True, on_delete=models.CASCADE)


class Trinity_interval(models.Model):
    starting = models.DateTimeField(verbose_name='Начало промежутка', blank=True, null=True)
    ending = models.DateTimeField(verbose_name='Конец промежутка', blank=True, null=True)
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE, null=True,
                                  blank=True)
    work_check = models.BooleanField(verbose_name='Оборудование работает?', null=True, blank=True)
    user_reason = models.ForeignKey(Reason, verbose_name='Причина оператора', on_delete=models.SET_NULL, null=True,
                                    blank=True, limit_choices_to={'is_operator': True})


class Repairer_master_reason(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name


class Repair_reason(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name


class Repair_rawdata(models.Model):
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата/Время')
    machines_id = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE, blank=True,
                                    null=True)
    card_id = models.CharField(max_length=70, verbose_name='ID карточки', blank=True, null=True)
    JOB_STATUSES = (
        (0, 'В рабочем состоянии'),
        (1, 'Сломан, необходим ремонт'),
        (2, 'В ремонте'),
    )
    repair_job_status = models.IntegerField(verbose_name='Статус оборудования', choices=JOB_STATUSES, null=False,
                                            default=0)
    repairer_id = models.ForeignKey('Repairer', verbose_name='Ремонтник', null=True, blank=True,
                                    on_delete=models.SET_NULL)
    repairer_master_reason = models.ForeignKey('Repairer_master_reason', verbose_name='Причина поломки', null=True,
                                               blank=True, on_delete=models.SET_NULL, default=None)
    repair_reason = models.ForeignKey('Repair_reason', verbose_name='Причина поломки', null=True, blank=True,
                                      on_delete=models.SET_NULL, default=None)
    repair_comment = models.TextField(verbose_name='Комментарий', blank=True, null=True, default=None)

    def __str__(self):
        return '{0}, {1}, {2}'.format(self.machines_id, self.date, self.card_id)


class Data_from_scan(models.Model):
    date = models.DateTimeField(auto_now=True, verbose_name='Дата/Время')
    mac_scan = models.CharField(max_length=70, verbose_name='MAC считывателя участка', blank=True, null=True)
    card_id = models.CharField(max_length=70, verbose_name='ID карточки')

    def __str__(self):
        return '{0}, {1}'.format(self.date, self.card_id)


class Repairer(models.Model):
    FIO = models.CharField(max_length=150, verbose_name='ФИО')
    card_id = models.CharField(max_length=70, verbose_name='ID карточки')

    def __str__(self):
        return '{0}'.format(self.FIO)


class Repair_statistics(models.Model):
    JOB_STATUSES = (
        (0, 'В рабочем состоянии'),
        (1, 'Сломан, необходим ремонт'),
        (2, 'В ремонте'),)
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name='Дата начала периода', blank=True, null=True)
    end_date = models.DateField(verbose_name='Дата конца периода', blank=True, null=True)
    start_time = models.TimeField(verbose_name='Время начала периода', blank=True, null=True)
    end_time = models.TimeField(verbose_name='Время конца периода', blank=True, null=True)
    de_facto = models.DurationField(verbose_name='Время работы с учетом расписания', blank=True, null=True)
    repair_job_status = models.IntegerField(verbose_name='Статус оборудования', choices=JOB_STATUSES, null=True,
                                            blank=True)


class Repair_history(models.Model):
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE)
    crush_date = models.DateTimeField(verbose_name='Дата и время поломки', blank=True, null=True, auto_now_add=True)
    repair_date = models.DateTimeField(verbose_name='Дата и время взятия в ремонт', blank=True, null=True,
                                       auto_now_add=True)
    return_to_work_date = models.DateTimeField(verbose_name='Дата и время возврата к работе', null=True, blank=True,
                                               auto_now_add=True)
    first_reason = models.ForeignKey(Repair_reason, verbose_name='Первичная причина', null=True, blank=True,
                                     on_delete=models.SET_NULL, default=None)
    master_reason = models.ForeignKey(Repairer_master_reason, verbose_name='Причина поломки', null=True, blank=True,
                                      on_delete=models.SET_NULL, default=None)
    repair_comment = models.TextField(verbose_name='Комментарий', blank=True, null=True, default=None)
    repairer = models.ForeignKey(Repairer, verbose_name='Ремонтник', null=True, blank=True, on_delete=models.SET_NULL)


class ClassifiedInterval(models.Model):
    # AVAILABLE_USER_REASON = lambda: [(str(r), str(r)) for r in Reason.objects.filter(is_operator=True)]
    start = models.DateTimeField(verbose_name='Начало периода')
    end = models.DateTimeField(verbose_name='Конец периода')
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE)
    is_zero = models.BooleanField(verbose_name='Нет данных', default=False, blank=True)
    automated_classification = models.ForeignKey(Reason, verbose_name='Вычисленная причина',
                                                 related_name='auto_reason', on_delete=models.PROTECT)
    user_classification = models.ForeignKey(Reason, verbose_name='Причина оператора',
                                            related_name='user_reason', on_delete=models.PROTECT, null=True,
                                            blank=True, limit_choices_to={'is_operator': True})
    user = models.ForeignKey(User, verbose_name='Указал причину', on_delete=models.SET_NULL,
                             null=True, blank=True)

    @property
    def length(self):
        """
        :return: int - amount of interval's minutes
        """
        delta = self.end - self.start
        return int(delta.total_seconds() // 60)

    @property
    def length_fmt(self):
        """
        formatted interval
        :return: string
        """
        delta = self.end - self.start
        return str(delta).replace('days', 'дн').replace('day', 'д')

    @property
    def get_link_graphdata(self):
        """
        get url page
        :return:
        """
        return ''

    @staticmethod
    def add_interval(equipment: Equipment, start: timezone.datetime, end: timezone.datetime, classification: Reason,
                     is_zero=False):
        """
        This function build chain of intervals to remove gaps between those and avoid overlappings
        result is adding or correction intervals in ClassifiedIntervals.objects
        """
        try:
            last_obj = ClassifiedInterval.objects.filter(equipment_id=equipment.id).order_by('-end')[0]
        except Exception as e:
            ci = ClassifiedInterval(equipment=equipment, start=start, end=end, automated_classification=classification,
                                    is_zero=is_zero)
            ci.save()
            return

        assert start >= last_obj.end, 'Overlapping do not allowed between intervals'
        assert start - datetime.timedelta(minutes=2) < last_obj.end, 'Large intervals without data do not allowed'

        # Without gaps
        start = last_obj.end

        if last_obj.automated_classification == classification:
            last_obj.end = end or timezone.now()
            last_obj.save()
            # update(last_obj.id, end=end or datetime.datetime.now())
        elif classification.is_working:  # working
            # need to decide if we can drop out previous idle interval due to duration
            try:
                prev_last_obj = ClassifiedInterval.objects.filter(equipment_id=equipment.id).order_by('-end')[1]
            except Exception as e:
                prev_last_obj = None
            if (prev_last_obj is not None
                    and prev_last_obj.automated_classification.is_working
                    and start - datetime.timedelta(minutes=equipment.allowed_idle_interval) < prev_last_obj.end
                    and not last_obj.is_zero):
                last_obj.delete()
                prev_last_obj.end = end or timezone.now()
                prev_last_obj.save()
            else:
                ci = ClassifiedInterval(start=start, end=end, equipment=equipment,
                                        automated_classification=classification, is_zero=is_zero)
                ci.save()
        else:
            ci = ClassifiedInterval(start=start, end=end, equipment=equipment,
                                    automated_classification=classification, is_zero=is_zero)
            ci.save()

    @staticmethod
    def remove_doubles():
        """
        remove doubles from intervals
        :return:
        """
        qs = ClassifiedInterval.objects.values('equipment', 'start').annotate(cnt=Count('id'),
                                                                              mid=Max('id')).filter(cnt__gt=1)
        ClassifiedInterval.objects.filter(id__in=qs.values('mid')).delete()

    @staticmethod
    def find_and_set_system_stopped_intervals():
        """
        if system stopped intervals would be zero and same start/end. When found such intervals set
        them as system fault
        :return:
        """
        # find special classified interval
        sys_stop_reason = Reason.objects.filter(code='999').first()
        if not sys_stop_reason:
            raise AttributeError('Причина 999 - системный сбой не найдена, продолжение невозможно')
        print(sys_stop_reason)

        # making query
        qs = ClassifiedInterval.objects.filter(is_zero=True).values('start', 'end').annotate(cnt=Count('id')) \
            .filter(cnt__gt=1)
        ClassifiedInterval.objects.filter(is_zero=True, start__in=qs.values('start'),
                                          end__in=qs.values('end')).update(automated_classification=sys_stop_reason)

    @staticmethod
    def get_statistics(start, end, workshop_id, by_workshop=False, equipment=None):
        '''
        calculates statistics for period
        :param start: start of period (string YYYY-mm-dd)
        :param end: end of period (string YYYY-mm-dd)
        :param by_workshop: if make grouping by workshop (Boolean)
        :param equipment: filter by equipment or not (int, equipment, array)
        :return: dict of statistics
        '''
        # check dates
        start_date = dateparse.parse_date(start)
        start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.datetime.min.time())) \
            if isinstance(start_date, datetime.date) else None
        if start_date is None:
            raise ValueError('Value {0} as start date is invalid, it should be YYYY-MM-DD formatted'.format(start))
        end_date = dateparse.parse_date(end)
        end_date = timezone.make_aware(datetime.datetime.combine(end_date, datetime.datetime.min.time())) \
            if isinstance(end_date, datetime.date) else None
        if end_date is None:
            raise ValueError('Value {0} as end date is invalid, it should be YYYY-MM-DD formatted'.format(end))

        # check equipment
        # 18.08.2020 Шабанов изменение филтрации поиска моделей
        if equipment is None:
            equipment_id_list = [eq.id for eq in Equipment.objects.filter(problem_machine=False, is_in_monitoring=True,
                                                                          workshop__in=workshop_id).order_by(
                '-workshop', 'id')]
        elif isinstance(equipment, list):
            equipment_id_list = ([eq.id for eq in equipment if isinstance(eq, Equipment)] +
                                 [id for id in equipment if isinstance(id, int)])
        elif isinstance(equipment, Equipment) or isinstance(equipment, int):
            equipment_id_list = [equipment.id if isinstance(equipment, Equipment) else equipment]
        else:
            raise ValueError('Equipment should be one of [list of equipment] or [list of ids] or equipment or id')

        statistics = {}
        total_auto_stats = {}
        total_user_stats = {}
        # cycle to get statistics
        for eid in equipment_id_list:
            intervals = ClassifiedInterval.objects.filter(equipment__problem_machine=False, equipment__id=eid,
                                                          end__gte=start_date, start__lte=end_date + datetime.timedelta(days=1))
            auto_stats = {}
            user_stats = {}
            for ci in intervals:
                start_i = max(ci.start, start_date)
                end_i = min(ci.end, end_date + datetime.timedelta(days=1))
                int_dur_min = int((end_i - start_i).total_seconds() // 60)
                auto_cl = str(ci.automated_classification) if ci.automated_classification else 'Неопределено'
                user_cl = str(ci.user_classification) if ci.user_classification else 'Не указано'

                auto_stats[auto_cl] = auto_stats.get(auto_cl, 0) + int_dur_min
                user_stats[user_cl] = user_stats.get(user_cl, 0) + \
                                      (int_dur_min if not ci.automated_classification.is_working else 0)

                # update total statistics
                total_auto_stats[auto_cl] = total_auto_stats.get(auto_cl, 0) + int_dur_min
                total_user_stats[user_cl] = total_user_stats.get(user_cl, 0) + \
                                            (int_dur_min if not ci.automated_classification.is_working else 0)

            statistics[str(Equipment.objects.filter(id=eid).first())] = {'auto_stats': auto_stats,
                                                                         'user_stats': user_stats}
        # end of cycle
        statistics['total'] = {'auto_stats': total_auto_stats, 'user_stats': total_user_stats}
        return statistics

    @staticmethod
    def get_report_data(start, end, workshop_id):
        '''
        calculates report
        :param start: start of period (string YYYY-mm-dd)
        :param end: end of period (string YYYY-mm-dd)
        :param by_workshop: if make grouping by workshop (Boolean)
        :return: dict of report
        '''

        equipment_id_list = [eq.id for eq in Equipment.objects.filter(problem_machine=False, is_in_monitoring=True,
                                                                      workshop__in=workshop_id).order_by(
            '-workshop', 'id')]

        statistics = {}
        if not equipment_id_list:
            statistics['day_stats'] = []
            statistics['total_workshop_user_data'] = {}
            return statistics
        else:
            # Check dates
            start_date = dateparse.parse_date(start);
            start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.datetime.min.time())) \
                if isinstance(start_date, datetime.date) else None
            if start_date is None:
                raise ValueError('Value {0} as start date is invalid, it should be YYYY-MM-DD formatted'.format(start))
            end_date = dateparse.parse_date(end)
            end_date = timezone.make_aware(datetime.datetime.combine(end_date, datetime.datetime.min.time())) \
                if isinstance(end_date, datetime.date) else None
            if end_date is None:
                raise ValueError('Value {0} as end date is invalid, it should be YYYY-MM-DD formatted'.format(end))

            # Cycle to get statistics
            delta = end_date - start_date
            days_stats = []

            for eid in equipment_id_list:
                percent_stats = []

                intervals_data = []

                user_stats_intervals = ClassifiedInterval.objects.filter(equipment__problem_machine=False,
                                                                         equipment__id=eid,
                                                                         end__gte=start_date, start__lte=end_date + datetime.timedelta(days=1) )
                user_stats = {}

                for ci in user_stats_intervals:
                    start_i = max(ci.start, start_date)
                    end_i = min(ci.end, end_date + datetime.timedelta(days=1))
                    int_dur_min = int((end_i - start_i).total_seconds() // 60)
                    user_cl = str(ci.user_classification) if ci.user_classification else '000 - Не указано'

                    user_stats[user_cl] = user_stats.get(user_cl, 0) + \
                                                        (int_dur_min if not ci.automated_classification.is_working else 0)

                user_stats_value = [sum(user_stats.values())]

                #  Calculation percent for reasons
                for k, v in user_stats.items():
                    if v == 0:
                        continue
                    else:
                        user_stats[k] = round(v / max(user_stats_value) * 100, 1)

                for day_count, i in enumerate(range(delta.days + 1)):
                    auto_stats = {}

                    intervals = ClassifiedInterval.objects.filter(equipment__problem_machine=False, equipment__id=eid,
                                                                  end__gte=start_date + datetime.timedelta(days=i),
                                                                  start__lte=start_date + datetime.timedelta(days=i + 1))
                    for c, ci in enumerate(intervals):
                        start_i = max(ci.start, start_date + datetime.timedelta(days=i))
                        end_i = min(ci.end, start_date + datetime.timedelta(days=i + 1))
                        int_dur_min = int((end_i - start_i).total_seconds() // 60)
                        auto_cl = str(ci.automated_classification) if ci.automated_classification else 'Неопределено'
                        auto_stats[auto_cl] = auto_stats.get(auto_cl, 0) + int_dur_min

                    if len(auto_stats) == 1:
                        if auto_stats.get('001 - Простой'):
                            percent_stats = 0
                        elif auto_stats.get('000 - Оборудование работает'):
                            percent_stats = 100
                    elif len(auto_stats) == 2:
                        total_dur_min = auto_stats.get('000 - Оборудование работает') + auto_stats.get('001 - Простой')
                        percent_stats = round(100 - auto_stats.get('001 - Простой') / total_dur_min * 100, 1)
                    # else:
                    #     print("Нет данных")
                    intervals_data.append(percent_stats)

                sort_user_stats = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)

                days_stats.append({
                    'workshop_id': Equipment.objects.filter(id=eid).values_list('workshop_id', flat=True).first(),
                    'code': Equipment.objects.filter(id=eid).values_list('code', flat=True).first(),
                    'model': Equipment.objects.filter(id=eid).values_list('model', flat=True).first(),
                    'days_percent': intervals_data,
                    'total_percent': round(mean(intervals_data), 1),
                    'user_stats': sort_user_stats
                })

            total_workshop_percent_dict = {}

            total_workshop_user_data = {}

            all_workshop_id = [x.workshop_number for x in Workshop.objects.all()]

            for workshop in all_workshop_id:
                total_user_stats = {}
                total_workshop_percent = 0
                total_workshop_count = 0
                # Total percent for period
                for item in days_stats:
                    if item['workshop_id'] == workshop:
                        total_workshop_percent += item['total_percent']
                        total_workshop_count += 1
                if total_workshop_percent == 0:
                    total_workshop_percent_dict[workshop] = 0
                else:
                    total_workshop_percent_dict[workshop] = round(total_workshop_percent / total_workshop_count, 1)

                workshop_equipment_id_list = Equipment.objects.values_list('id', flat=True).filter(problem_machine=False,
                                                                                                   is_in_monitoring=True,
                                                                                                   workshop_id=workshop)

                for eid in workshop_equipment_id_list:
                    intervals = ClassifiedInterval.objects.filter(equipment__problem_machine=False, equipment__id=eid,
                                                                  end__gte=start_date, start__lte=end_date + datetime.timedelta(days=1))
                    for ci in intervals:
                        start_i = max(ci.start, start_date)
                        end_i = min(ci.end, end_date + datetime.timedelta(days=1))
                        int_dur_min = int((end_i - start_i).total_seconds() // 60)
                        user_cl = str(ci.user_classification) if ci.user_classification else '000 - Не указано'

                        total_user_stats[user_cl] = total_user_stats.get(user_cl, 0) + \
                                                    (int_dur_min if not ci.automated_classification.is_working else 0)

                total_workshop_user_data[workshop] = total_user_stats

            statistics['day_stats'] = days_stats
            statistics['total_workshop_user_data'] = total_workshop_user_data
            return statistics


class GraphicsData(models.Model):
    date = models.DateTimeField(verbose_name='Дата и время')
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.PROTECT)
    value = models.FloatField(verbose_name='Значение')

    @staticmethod
    def clear_doubles():
        qs = GraphicsData.objects.values('date', 'equipment').annotate(cnt=Count('id'),
                                                                       mid=Max('id')).filter(cnt__gt=1)
        GraphicsData.objects.filter(id__in=qs.values('mid')).delete()


class Semaphore(models.Model):
    name = models.CharField(max_length=50, verbose_name='Семафор')
    is_locked = models.BooleanField(verbose_name='Заблокировано', default=False)
    locked_when = models.DateTimeField(verbose_name='Когда заблокировано', default=timezone.now)
    alert_interval = models.IntegerField(verbose_name='Количество минут до предупреждения', default=15)

    def get_locked_interval(self):
        if self.is_locked:
            delta = timezone.now() - self.locked_when
            return int(delta.total_seconds() // 60)
        else:
            return 0

    def __str__(self):
        if self.is_locked:
            to_s = '{0}, locked {1} min'.format(self.name, self.get_locked_interval())
        else:
            to_s = '{0}, unlocked'.format(self.name)
        return to_s


# Дополнительная модель, связанная с моделью User
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=12)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Модель кода безопасности
class Code(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    code = models.CharField(max_length=4)
