# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Count, Max
from django.contrib.auth.models import User
from django.utils import timezone, dateparse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import datetime


# Create your models here.


class Reason(models.Model):
    code = models.CharField(max_length=10, verbose_name='Код')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    is_working = models.BooleanField(verbose_name='Работа', default=False)
    is_operator = models.BooleanField(verbose_name='Указывается оператором', default=False)

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


class Equipment(models.Model):
    WORKSHOP_CHOICES = (
        ('6', 'цех 6'),
        ('7', 'цех 7'),
        ('8', 'цех 8'),
        ('9', 'цех 9'),
        ('11', 'цех 11'),
        ('14', 'цех 14'),
        ('20', 'цех 20'),
        ('26', 'цех 26'),
    )
    TIMETABLE_CHOICES = (
        ('8/5', '8 часов с выходными'),
        ('12/5', '12 часов с выходными'),
        ('24/5', 'круглосуточно с выходными'),
        ('24/7', 'круглосуточно без выходных'),
    )
    AVAILABLE_MACS = lambda: [(m.mac_address, m.mac_address)
                              for m in RawData.objects.filter(date__gte=timezone.localdate())
                                  .order_by('mac_address').distinct('mac_address')]
    AVAILABLE_CHANNELS = lambda: [(m.channel, m.channel)
                                  for m in RawData.objects.filter(date__gte=timezone.localdate()).distinct('channel')]
    workshop = models.CharField(max_length=20, verbose_name='Цех', choices=WORKSHOP_CHOICES)
    code = models.CharField(max_length=10, verbose_name='Инвентарный номер')
    model = models.CharField(max_length=20, verbose_name='Модель')
    description = models.TextField(max_length=1000, verbose_name='Описание', null=True, blank=True)
    timetable = models.CharField(max_length=30, verbose_name='Расписание', choices=TIMETABLE_CHOICES)
    master = models.ForeignKey(Participant, on_delete=models.PROTECT)
    xbee_mac = models.CharField(max_length=25, verbose_name='MAC модема',
                                choices=AVAILABLE_MACS(), null=True, blank=True)
    main_channel = models.CharField(max_length=5, verbose_name='Канал', choices=AVAILABLE_CHANNELS(),
                                    null=True, blank=True)
    idle_threshold = models.IntegerField(verbose_name='Порог включения', default=100)
    no_load_threshold = models.IntegerField(verbose_name='Порог холостого хода', default=110)
    allowed_idle_interval = models.IntegerField(verbose_name='Допустимый простой, мин', default=15)
    # image = models.ImageField(blank=True, null=True)
    # sm_image = models.ImageField(blank=True, null=True)

    def __str__(self):
        return '{0} - {1}, цех {2}'.format(self.code, self.model, self.workshop)


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
        if equipment is None:
            equipment_id_list = [eq.id for eq in Equipment.objects.all()]
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
                user_stats[user_cl] = user_stats.get(user_cl, 0) + int_dur_min

                # update total statistics
                total_auto_stats[auto_cl] = total_auto_stats.get(auto_cl, 0) + int_dur_min
                total_user_stats[user_cl] = total_user_stats.get(user_cl, 0) + int_dur_min

            statistics[str(Equipment.objects.filter(id=eid).first())] = {'auto_stats': auto_stats,
                                                                         'user_stats': user_stats}
        # end of cycle
        statistics['total'] = {'auto_stats' : total_auto_stats, 'user_stats': user_stats}
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

    def __str__(self):
        return ('{0}-{1}:(1-я смена:{2}-{3})'.format(self.day_of_week_start, self.day_of_week_end,
                                                     self.start_time1.strftime('%H:%M'),
                                                     self.end_time1.strftime('%H:%M')))


class Timetable(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название расписания:')
    pre_holiday_short = models.BooleanField(verbose_name='В предпразничные дни на смены час короче',
                                            auto_created=True)

    def __str__(self):
        return self.name


class TimetableContent(models.Model):
    timetable = models.ForeignKey(Timetable, verbose_name='Расписание', on_delete=models.CASCADE)
    details = models.ForeignKey(TimetableDetail, verbose_name='Детали', on_delete=models.CASCADE)


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
