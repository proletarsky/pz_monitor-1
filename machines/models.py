# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User
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
                              for m in RawData.objects.order_by('mac_address').distinct('mac_address')]
    AVAILABLE_CHANNELS = lambda: [(m.channel, m.channel)
                                  for m in RawData.objects.distinct('channel')]
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

    def __str__(self):
        return '{0} - {1}, цех {2}'.format(self.code, self.model, self.workshop)


class ClassifiedInterval(models.Model):
    # AVAILABLE_USER_REASON = lambda: [(str(r), str(r)) for r in Reason.objects.filter(is_operator=True)]
    start = models.DateTimeField(verbose_name='Начало периода')
    end = models.DateTimeField(verbose_name='Конец периода')
    equipment = models.ForeignKey(Equipment, verbose_name='Оборудование', on_delete=models.CASCADE)
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
        return delta.days * 60 * 24 + delta.hours * 60 + delta.minutes

    @property
    def length_fmt(self):
        """
        formatted interval
        :return: string
        """
        delta = self.end - self.start
        return str(delta).replace('days', 'дн').replace('day', 'д')

    @staticmethod
    def add_interval(equipment: Equipment, start: timezone.datetime, end: timezone.datetime, classification: Reason):
        """
        This function build chain of intervals to remove gaps between those and avoid overlappings
        result is adding or correction intervals in ClassifiedIntervals.objects
        """
        try:
            last_obj = ClassifiedInterval.objects.filter(equipment_id=equipment.id).order_by('-end')[0]
        except Exception as e:
            ci = ClassifiedInterval(equipment=equipment, start=start, end=end, automated_classification=classification)
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
                    and start - datetime.timedelta(minutes=equipment.idle_threshold) < prev_last_obj.end):
                last_obj.delete()
                prev_last_obj.end = end or timezone.now()
                prev_last_obj.save()
            else:
                ci = ClassifiedInterval(start=start, end=end, equipment=equipment,
                                        automated_classification=classification)
                ci.save()
        else:
            ci = ClassifiedInterval(start=start, end=end, equipment=equipment,
                                    automated_classification=classification)
            ci.save()


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


