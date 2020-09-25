# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from machines.time_helpers import CurrentDayType, get_duration_minutes

from django.db import models
from django.db.models import Count, Max
from django.contrib.auth.models import User
from django.utils import timezone, dateparse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ValidationError
import datetime

# Create your models here.


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
        elif todayType == 0 or todayType == 2:    # common working day or eve holiday
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
                    time_intervals = [(foundTD.start_time1, datetime.time(foundTD.end_time1.hour-sub_hour,
                                                                          foundTD.end_time1.minute, 0))]
                else:
                    time_intervals = [(foundTD.start_time1, foundTD.lunch_start1),
                                      (foundTD.lunch_end1, datetime.time(foundTD.end_time1.hour-sub_hour,
                                                                         foundTD.end_time1.minute, 0))]
                if foundTD.start_time2:
                    if foundTD.lunch_start2 is None:
                        time_intervals += [(foundTD.start_time2, datetime.time(foundTD.end_time2.hour-sub_hour,
                                                                               foundTD.end_time2.minute, 0))]
                    else:
                        time_intervals += [(foundTD.start_time2, foundTD.lunch_start2),
                                           (foundTD.lunch_end2, datetime.time(foundTD.end_time2.hour-sub_hour,
                                                                              foundTD.end_time2.minute, 0))]
                if foundTD.start_time3:
                    if foundTD.lunch_start3 is None:
                        time_intervals += [(foundTD.start_time3, datetime.time(foundTD.end_time3.hour-sub_hour,
                                                                               foundTD.end_time3.minute, 0))]
                    else:
                        time_intervals += [(foundTD.start_time3, foundTD.lunch_start3),
                                           (foundTD.lunch_end3, datetime.time(foundTD.end_time3.hour-sub_hour,
                                                                              foundTD.end_time3.minute, 0))]
            return time_intervals
        else:
            return []


class TimetableContent(models.Model):
    timetable = models.ForeignKey(Timetable, related_name='timetable', verbose_name='Расписание',
                                     on_delete=models.DO_NOTHING)
    details = models.ForeignKey(TimetableDetail, related_name='detail', verbose_name='Детали', on_delete=models.DO_NOTHING)


#12.08.2020 Шабанов добавление новых моделей
class Workshop(models.Model):
    workshop_number = models.IntegerField(verbose_name='Номер цеха',primary_key=True)
    name = models.CharField(max_length=50, verbose_name='Наименование')
    foreman = models.CharField(max_length=50,verbose_name='Начальник цеха',null=True,blank=True)

    def __str__(self):
        return str(self.workshop_number)


class Area(models.Model):
    workshop=models.ForeignKey(Workshop,verbose_name='Цех',on_delete=models.SET_NULL,null=True,blank=True)
    name=models.CharField(max_length=50,verbose_name='Наименование')
    area_number=models.IntegerField(verbose_name='Номер участка',null=True,blank=True)
    mac_scan = models.CharField(max_length=70,verbose_name='MAC считывателя участка',blank=True,null=True)
    green_card_id=models.CharField(max_length=70,verbose_name='ID зеленой карточки')

    def __str__(self):
        return self.name+' цеха №'+str(self.workshop)

class Complex(models.Model):
    name=models.CharField(max_length=70,verbose_name='Наименование')
    descr=models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name

class Equipment(models.Model):
    
    TIMETABLE_CHOICES = (
        ('8/5', '8 часов с выходными'),
        ('12/5', '12 часов с выходными'),
        ('24/5', 'круглосуточно с выходными'),
        ('24/7', 'круглосуточно без выходных'),
    )
    AVAILABLE_MACS = lambda: [(m.mac_address, m.mac_address)
                              for m in RawData.objects.all().distinct('mac_address')]
    AVAILABLE_CHANNELS = lambda: [(m.channel, m.channel)
                                  for m in RawData.objects.filter(date__gte=timezone.localdate()).distinct('channel')]
    #Шабанов изменение структуры модели - поле "Цех" больше не является строкой, здесь теперь хранятся ссылки на объекты типа цех из таблицы Workshop
    workshop = models.ForeignKey(Workshop,verbose_name='Цех',on_delete=models.PROTECT,blank=True,null=True)
    #workshop=models.IntegerField(verbose_name='Цех')
    area = models.ForeignKey(Area,verbose_name='Участок',on_delete=models.PROTECT,null=True,blank=True)
    code = models.CharField(max_length=10, verbose_name='Инвентарный номер')
    model = models.CharField(max_length=20, verbose_name='Модель')
    image=models.ImageField(blank=True, upload_to='machines', verbose_name='Фото оборудования')
    description = models.TextField(max_length=1000, verbose_name='Описание', null=True, blank=True)
    timetable = models.CharField(max_length=30, verbose_name='Расписание', choices=TIMETABLE_CHOICES)
    master = models.ForeignKey(Participant, on_delete=models.PROTECT)
    machine_or_furnace_sign = models.BooleanField(verbose_name='Оборудование является станком', default=True)
    xbee_mac = models.CharField(max_length=25, verbose_name='MAC модема',
                                #choices=AVAILABLE_MACS(), -- замена выпадающего списка на текстовое поле
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
        (0,'В рабочем состоянии'),
        (1,'Сломан, необходим ремонт'),
        (2,'В ремонте'),
    )
    repair_job_status = models.IntegerField(verbose_name='Статус оборудования', choices=JOB_STATUSES,null=False,default=0)
    red_card_id = models.CharField(max_length=70,verbose_name='ID красной карточки',default=1000000000)
    in_complex=models.ForeignKey(Complex,verbose_name='Входит в комплекс',on_delete=models.DO_NOTHING,null=True,blank=True)
    # image = models.ImageField(blank=True, null=True)
    # sm_image = models.ImageField(blank=True, null=True)

    def __str__(self):
        if self.area is None:
            return '{0} - {1}, цех {2}'.format(self.code, self.model,self.workshop)
        else:
            return '{0} - {1}, {2}'.format(self.code, self.model,self.area)


class Repair_reason(models.Model):
	name = models.CharField(max_length=100,verbose_name='Наименование')
	description = models.TextField(verbose_name='Описание')

	def __str__(self):
		return self.name



class Repair_rawdata(models.Model):
    date = models.DateTimeField(auto_now=True,verbose_name='Дата/Время')
    machines_id = models.ForeignKey(Equipment,verbose_name='Оборудование',on_delete=models.CASCADE, blank=True,null=True)
    card_id = models.CharField(max_length=70,verbose_name='ID карточки',blank=True,null=True)
    JOB_STATUSES = (
        (0,'В рабочем состоянии'),
        (1,'Сломан, необходим ремонт'),
        (2,'В ремонте'),
    )
    repair_job_status = models.IntegerField(verbose_name='Статус оборудования', choices=JOB_STATUSES,null=False,default=0)
    repairer_id = models.ForeignKey('Repairer',verbose_name='Ремонтник', null=True,blank=True,on_delete=models.SET_NULL)
    repair_reason = models.ForeignKey('Repair_reason',verbose_name='Причина поломки',null=True,blank=True,on_delete=models.SET_NULL)

    def __str__(self):
        return '{0}, {1}, {2}'.format(self.machines_id,self.date,self.card_id)


class Data_from_scan(models.Model):
    date = models.DateTimeField(auto_now=True,verbose_name='Дата/Время')
    mac_scan = models.CharField(max_length=70,verbose_name='MAC считывателя участка',blank=True,null=True)
    card_id = models.CharField(max_length=70,verbose_name='ID карточки')

    def __str__(self):
        return '{0}, {1}'.format(self.date, self.card_id)

class Repairer(models.Model):
    FIO = models.CharField(max_length=150,verbose_name='ФИО')
    card_id=models.CharField(max_length=70,verbose_name='ID карточки')

    def __str__(self):
        return '{0}'.format(self.FIO)



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
                     is_zero = False):
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
    def get_statistics(start, end, by_workshop=False, equipment=None):
        '''
        calculates statistics for period
        :param start: start of period (string YYYY-mm-dd)
        :param end: end of period (string YYYY-mm-dd)
        :param by_workshop: if make grouping by workshop (Boolean)
        :param equipment: filter by equipment or not (int, equipment, array)
        :return: dict of statistics
        '''
        # check dates
        start_date = dateparse.parse_date(start);
        start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.datetime.min.time())) \
            if isinstance(start_date, datetime.date) else None
        if start_date is None:
            raise ValueError('Value {0} as start date is invalid, it should be YYYY-MM-DD formatted'.format(start))
        end_date = dateparse.parse_date(end)
        end_date = timezone.make_aware(datetime.datetime.combine(end_date, datetime.datetime.min.time()))\
            if isinstance(end_date, datetime.date) else None
        if end_date is None:
            raise ValueError('Value {0} as end date is invalid, it should be YYYY-MM-DD formatted'.format(end))

        # check equipment
        #18.08.2020 Шабанов изменение филтрации поиска моделей
        if equipment is None:
            equipment_id_list = [eq.id for eq in Equipment.objects.filter(is_in_monitoring=True).order_by('-workshop', 'id')]
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
            intervals = ClassifiedInterval.objects.filter(equipment__id=eid, end__gte=start_date, start__lte=end_date)
            # auto_reasons = intervals.values('automated_classification').distinct()
            # user_reasons = intervals.values('user_classification').distinct()
            # setup auto_stats and user_stats (fills zero)
            # auto_stats = {str(reason['automated_classification']): 0 for reason in auto_reasons}
            # user_stats = {str(reason['user_classification']): 0 for reason in user_reasons if reason}
            auto_stats = {}
            user_stats = {}
            for ci in intervals:
                start_i = max(ci.start, start_date)
                end_i = min(ci.end, end_date)
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
        statistics['total'] = {'auto_stats' : total_auto_stats, 'user_stats': total_user_stats}
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
            return int(delta.total_seconds()//60)
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
    code=models.CharField(max_length=4)
