# machines/tasks.py
from __future__ import absolute_import, unicode_literals
import sys, os
import numpy as np
import logging
from celery import task
from .models import Equipment, ClassifiedInterval, Reason, RawData, Semaphore, GraphicsData
from qsstats import QuerySetStats
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone, dateparse
from datetime import datetime, timedelta
import pytz

from django.contrib.auth.models import User
import psycopg2 as ps
from datetime import timedelta

# logger = logging.getLogger(__name__)
HOST = '192.168.7.75'
DB = 'moncopy'
USER = 'djangouser'
PWD = 'password'

cmd = 'select ci.start, ci.end, ci.automated_classification_id, ci.equipment_id, ci.user_id '\
        'from machines_classifiedinterval ci where ci.user_classification_id is not null'


@task()
def test_task():
    print('############ It is the first task! ####################')


@task()
def update_intervals():
    """
    periodic function to transform RawData to GraphicsData and ClassifiedIntervals
    :return:
    """
    # Check if ClassifiedIntervals doesnt locked
    lock = Semaphore.objects.filter(name=ClassifiedInterval.__name__).first()
    if lock and lock.is_locked:
        # TODO - check if locked period is not too long
        print('Locked!!!')
        return  # Locked - nothing to do

    available_reasons = Reason.objects.filter(code__in=['000', '001', '002']).order_by('code')
    for eq in Equipment.objects.all():
        try:
            last_date = ClassifiedInterval.objects.filter(equipment_id__exact=eq.id).order_by('-end').first().end
        except Exception:
            try:
                last_date = RawData.objects.filter(mac_address=eq.xbee_mac).order_by('date').first().date
            except Exception:
                continue  # No data at all

        # print(f'eq = {eq}; last_date = {last_date}')

        qs = RawData.objects.filter(mac_address=eq.xbee_mac, channel=eq.main_channel, date__gte=last_date)

        ts = QuerySetStats(qs, date_field='date', aggregate=Avg('value')).time_series(start=last_date,
                                                                                      end=timezone.now(),
                                                                                      interval='minutes')
        # print(ts[0][0], ts[-1][0])
        prev_reason = None
        start = ts[0][0]
        for t in ts:
            if t[1] >= eq.no_load_threshold:
                cur_reason = available_reasons[0]
            else:
                cur_reason = available_reasons[1]

            # Do not forget to apply timetables

            if prev_reason is not None and (cur_reason.id != prev_reason.id or t[0] == ts[-1][0]):
                # print('adding interval {0} {1} {2}'.format(start, t[0], cur_reason))
                try:
                    ClassifiedInterval.add_interval(start=start, end=t[0], equipment=eq,
                                                    classification=prev_reason)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    #logger.error('{0}, {1}, {2}\n{3}'.format(exc_type, fname,
                    #                                                        exc_tb.tb_lineno, e))
                    print('{0}, {1}, {2}\n{3}'.format(exc_type, fname, exc_tb.tb_lineno, e))
                    return
                prev_reason = cur_reason
                start = t[0]
            else:
                prev_reason = cur_reason

        # clear data in RawData between last_date and date_from
        last_gd = GraphicsData.objects.filter(equipment=eq).order_by('-date').first()
        if not last_gd:
            # No GraphicsData at all
            date_from = RawData.objects.filter(mac_address=eq.xbee_mac, channel=eq.main_channel) \
                                        .order_by('date').first().date
        else:
            date_from = last_gd.date if last_gd else last_date
            date_from += timedelta(minutes=1)
        if date_from < last_date:
            qs = RawData.objects.filter(mac_address=eq.xbee_mac, channel=eq.main_channel,
                                        date__gte=date_from) # Dont need to add last_date - in't error!
            # print(date_from, last_date)
            # print(last_date)
            ts = QuerySetStats(qs, date_field='date',
                               aggregate=Avg('value')).time_series(start=date_from, end=last_date, interval='minutes')
            # print(ts)
            with transaction.atomic():
                # write all grouped RawData object into GraphicsData and delete RawData
                GraphicsData.objects.bulk_create(
                    [GraphicsData(equipment=eq, date=t[0], value=t[1]) for t in ts]
                )
                # clear RawData
                RawData.objects.filter(mac_address=eq.xbee_mac, date__gte=date_from,
                                       date__lte=last_date+timedelta(minutes=1)).delete()
        else:
            print('Nothing to update')


@task()
def rebuild_intervals(equipment=None, start=None, end=None):
    """
    use this function to rebuild intervals after changing levels or found errors
    :param equipment: model.Equipment object or pk
    :param start: start datetime, if None - from very beginning
    :param end: end detatime, if None - till now
    :return: None
    """
    try:
        # First of all lock ClassifiedInterval update
        semaphores = Semaphore.objects.filter(name=ClassifiedInterval.__name__)
        if semaphores:
            lock = semaphores.first()
            lock.lock_when = timezone.now()
            lock.is_locked = True
        else:
            lock = Semaphore(name=ClassifiedInterval.__name__, is_locked=True)
        lock.save()

        # Next define set of ClassifiedIntervals to rebuild
        if equipment is None:
            equipment_set = Equipment.objects.all()
        elif isinstance(equipment, Equipment):
            equipment_set = [equipment]
        elif isinstance(equipment, int):
            equipment_set = Equipment.objects.filter(id=equipment)
        else:
            raise AttributeError('Invalid equipment {0}. It must be Equipment object or int'.format(equipment))

        # Next define start and end values
        if start is None:
            macs = [x.xbee_mac for x in equipment_set]
            # DONE - change to another object
            first_rd = RawData.objects.filter(mac_address__in=macs).order_by('date').first()
            first_gd = GraphicsData.objects.filter(equipment__in=equipment_set).order_by('date').first()
            period_start = first_gd.date if first_gd is not None else first_rd.date
        elif not isinstance(start, datetime):
            period_start = dateparse.parse_date(start) or dateparse.parse_datetime(start)
            if period_start is None:
                raise AttributeError('Wrong date or datetime format {0}. Use standard one'.format(start))
        else:
            period_start = start
        if end is None:
            period_end = timezone.now()
        elif not isinstance(end, datetime):
            period_end = dateparse.parse_date(end) or dateparse.parse_datetime(end)
            if period_end is None:
                raise AttributeError('Wring date or datetime format {0}. Use standard one'.format(end))
        else:
            period_end = end

        print(period_start, period_end)

        # Main cycle
        detected_intervals = []
        for equip in equipment_set:
            # DONE  - will not working with RawData!
            rd_start = RawData.objects.filter(mac_address=equip.xbee_mac, date__gte=period_start,
                                              date__lte=period_end).order_by('date').first()
            if rd_start: # RawData are present
                rd_end = RawData.objects.filter(mac_address=equip.xbee_mac, date__gte=period_start,
                                                date__lte=period_end).order_by('date').last()

                qs = RawData.objects.filter(mac_address=equip.xbee_mac, channel=equip.main_channel,
                                            date__gte=rd_start.date, date__lte=rd_end.date).order_by('date')
                ts = QuerySetStats(qs, date_field='date', aggregate=Avg('value')).time_series(start=rd_start.date,
                                                                                              end=period_end,
                                                                                              interval='minutes')
                # Any possible RawData should transform to GraphicsData
                with transaction.atomic():
                    # Remove possible doubles
                    GraphicsData.objects.filter(equipment=equip, date__gte=ts[0][0], date__lt=ts[-1][0]).delete()
                    # Create new data from ts
                    GraphicsData.objects.bulk_create([GraphicsData(equipment=equip, date=t[0],
                                                                   value=t[1]) for t in ts])
                    # Remove data from RawData (including not used channels)
                    RawData.objects.filter(mac_address=equip.xbee_mac, date__gte=rd_start.date,
                                           date__lte=rd_end.date).delete()

            # Rebuild time series
            qs = GraphicsData.objects.filter(equipment=equip, date__gte=period_start,
                                             date__lt=period_end).order_by('date')
            ts = [[d.date, d.value] for d in qs]
            cur_start = ts[0][0]
            cur_is_work = ts[0][1] >= equip.no_load_threshold
            intervals = []
            for i, t in enumerate(ts[1:]):
                is_work = (t[1] >= equip.no_load_threshold)
                if is_work != cur_is_work or t[0] == ts[-1][0]:
                    if t[0] == ts[-1][0]:   # last element
                        interval = {
                            'start': cur_start,
                            'end': t[0],
                            'is_work': cur_is_work
                        }
                        if not cur_is_work:
                            minutes = int((t[0] - cur_start).total_seconds()//60)
                            if np.mean([x[1] for x in ts[i-minutes:i]]) < 5:
                                interval['is_zero'] = 0
                        intervals.append(interval)
                    elif is_work:     # change from 0 to 1
                        delta = t[0] - cur_start
                        minutes = int(delta.total_seconds() // 60)
                        if minutes >= equip.allowed_idle_interval or not intervals or t[0] == ts[-1][0]:
                            interval = {
                                'start': cur_start,
                                'end': t[0],
                                'is_work': False,
                            }
                            if minutes <= i and i > 0:
                                # If interval has no data (mean value is almost 0)
                                if np.mean([x[1] for x in ts[i-minutes:i]]) < 5:
                                    interval['is_zero'] = True
                                # If interval with user data exists, save reason and user
                                interval_qs = ClassifiedInterval.objects.filter(equipment=equip,
                                        start__range=(cur_start-timedelta(minutes=3), cur_start+timedelta(minutes=3)),
                                        end__range=(t[0]-timedelta(minutes=3), t[0]+timedelta(minutes=3)),
                                        automated_classification__is_working=False,
                                        user_classification__isnull=False)
                                if interval_qs:
                                    interval_db = interval_qs.first()
                                    interval['user_classification'] = interval_db.user_classification
                                    interval['user'] = interval_db.user
                            intervals.append(interval)
                            cur_start = t[0]
                            cur_is_work = True
                        else: # remove current state, pretend to be working
                            cur_start = intervals[-1]['start']
                            cur_is_work = True
                            del intervals[-1]
                    else:
                        interval = {
                            'start': cur_start,
                            'end': t[0],
                            'is_work': True
                        }
                        intervals.append(interval)
                        cur_start = t[0]
                        cur_is_work = False
            # debugging information - output
            # print(intervals)
            # durs = [(x['end'] - x['start']).total_seconds()//60 for x in intervals if not x['is_work']]
            # print(durs)
            # end debugging information, creating intervals
            left_interval = ClassifiedInterval.objects.filter(equipment=equip,
                                                              start__lt=period_start,
                                                              end__gte=period_start).first()
            right_interval = ClassifiedInterval.objects.filter(equipment=equip,
                                                               start__lte=period_end,
                                                               end__gt=period_end).first()
            int_start = left_interval.end if left_interval else period_start
            int_end = right_interval.start if right_interval else period_end
            with transaction.atomic():
                # Remove intervals between int_start and int_end
                ClassifiedInterval.objects.filter(equipment=equip, start__gte=int_start,
                                                  end__lte=int_end).delete()
                # very special case - left and rights intervals are the same
                if left_interval and right_interval and left_interval.pk == right_interval.pk:
                    if len(intervals) == 1 and intervals[0]['is_work'] == left_interval.is_work:
                        continue    # Nothing to do
                    else:   # Need to create new right interval
                        end_interval = left_interval.end
                        left_interval.end = intervals[0]['start']
                        left_interval.save()
                        right_interval = ClassifiedInterval(equipment=equip,
                                    automated_classification=left_interval.automated_classification,
                                    user_classification=left_interval.user_classification,
                                    is_zero=left_interval.is_zero,
                                    start=intervals[-1]["end"],
                                    end=end_interval,
                                    user=left_interval.user)
                        right_interval.save()
                # try to join left interval
                if left_interval:
                    if intervals[0]['is_work'] == left_interval.automated_classification.is_working:
                        left_interval.end = intervals[0]['end']
                        left_interval.save()
                        del intervals[0]
                    else:
                        left_interval.end = intervals[0]['start']
                        left_interval.save()
                # try to join right interval
                if right_interval:
                    if intervals[-1]['is_work'] == right_interval.automated_classification.is_working:
                        right_interval.start = intervals[-1]['start']
                        right_interval.save()
                        del intervals[-1]
                    else:
                        right_interval.start = intervals[-1]['end']
                        right_interval.save()
                # prepare automated classification
                available_reasons = Reason.objects.filter(code__in=['000', '001', '002']).order_by('code')
                ClassifiedInterval.objects.bulk_create(
                    [ClassifiedInterval(equipment=equip, start=ci['start'], end=ci['end'],
                                        is_zero=ci.get('is_zero', False),
                                        user_classification=ci.get('user_classification'),
                                        user=ci.get('user'),
                                        automated_classification=(available_reasons[0] if ci['is_work']
                                                                  else available_reasons[1])) for ci in intervals]
                ) # End of bulk_create
        # End of main loop

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
    finally:
        semaphore = Semaphore.objects.filter(name=ClassifiedInterval.__name__).first()
        if semaphore:
            semaphore.is_locked = False
            semaphore.save()
        else:
            print('Can not unlock!!!!!')


@task()
def fixit():
    start = dateparse.parse_datetime('2019-07-04T21:45:00+03')
    end = dateparse.parse_datetime('2019-07-05T12:10:00+03')
    if start and end:
        rebuild_intervals(start=start, end=end)

@task()
def restore_ci():
    print('Restore ClassifiedIntervals user data')

    conn = ps.connect(host=HOST, database=DB, user=USER, password=PWD)
    c = conn.cursor()
    c.execute(cmd)
    qs = c.fetchall()
    print('fetched {0} rows'.format(len(qs)))

    for data in qs:
        start, end, auto_cl, eq_id, user_id = data
        print(start, type(start))
        start_st = start.astimezone(pytz.UTC) - timedelta(minutes=2)
        start_en = start.astimezone(pytz.UTC) + timedelta(minutes=2)
        end_st = end.astimezone(pytz.UTC) - timedelta(minutes=2)
        end_en = end.astimezone(pytz.UTC) + timedelta(minutes=2)
        cis = ClassifiedInterval.objects.filter(equipment__id=eq_id,
                                                 automated_classification_id=auto_cl,
                                                 start__range = (start_st, start_en),
                                                 end__range=(end_st, end_en))
        if cis:
            user_reason = Reason.objects.get(id=user_id)
            user = User.objects.get(id=user_id)
            print('user = {0}'.format(user))
            for ci in cis:
                ci.user_classification = user_reason
                ci.user = user
                ci.save()
        else:
            print('Interval {0}-{1} for equipment {2} not found!'.format(start, end, eq_id))
