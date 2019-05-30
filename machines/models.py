# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Reason(models.Model):
    code = models.CharField(max_length=10, verbose_name='Код')
    description = models.TextField(max_length=1000, verbose_name='Описание')

    def __str__(self):
        return ('{0} - {1}'.format(self.code, self.description)).encode('utf-8')


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
        return string.encode('utf-8')


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
    workshop = models.CharField(max_length=20, verbose_name='Цех', choices=WORKSHOP_CHOICES)
    code = models.CharField(max_length=10, verbose_name='Инвентарный номер')
    model = models.CharField(max_length=20, verbose_name='Модель')
    description = models.TextField(max_length=1000, verbose_name='Описание', null=True, blank=True)
    timetable = models.CharField(max_length=30, verbose_name='Расписание', choices=TIMETABLE_CHOICES)
    master = models.ForeignKey(Participant, on_delete=models.PROTECT)
    xbee_mac = models.CharField(max_length=15, verbose_name='MAC модема', null=True, blank=True)

    def __str__(self):
        return ('{0} - {1}, цех {2}'.format(self.code, self.model, self.workshop)).encode('utf-8')


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
                                                     self.end_time1.strftime('%H:%M'))).encode('utf-8')


class Timetable(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название расписания:')
    pre_holiday_short = models.BooleanField(verbose_name='В предпразничные дни на смены час короче',
                                            auto_created=True)

    def __str__(self):
        return self.name.encode('utf-8')


class TimetableContent(models.Model):
    timetable = models.ForeignKey(Timetable, verbose_name='Расписание', on_delete=models.CASCADE)
    details = models.ForeignKey(TimetableDetail, verbose_name='Детали', on_delete=models.CASCADE)


class RawData(models.Model):
    date = models.DateTimeField(auto_now=True)
    mac_address = models.CharField(max_length=25)
    channel = models.CharField(max_length=5, null=True)
    value = models.FloatField()
    ip = models.CharField(max_length=20, null=True)


