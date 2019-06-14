# machines/tasks.py
from __future__ import absolute_import, unicode_literals
from celery import task
from .models import Equipment, ClassifiedInterval, Reason, RawData
from qsstats import QuerySetStats
from django.db.models import Avg
from django.utils import timezone


@task()
def test_task():
    print('############ It is the first task! ####################')


@task()
def update_intervals():
    available_reasons = Reason.objects.filter(code__in=['000', '001', '002']).order_by('code')
    for eq in Equipment.objects.all():
        try:
            last_date = ClassifiedInterval.objects.filter(equipment_id__exact=eq.id).order_by('-end').first().end
        except Exception:
            try:
                last_date = RawData.objects.filter(mac_address=eq.xbee_mac).order_by('date').first().date
            except Exception:
                continue  # No data at all

        print(last_date)

        qs = RawData.objects.filter(mac_address=eq.xbee_mac, channel=eq.main_channel, date__gte=last_date)

        ts = QuerySetStats(qs, date_field='date', aggregate=Avg('value')).time_series(start=last_date,
                                                                                      end=timezone.now(),
                                                                                      interval='minutes')
        print(ts[-1][0], ts[-1][1])
        prev_reason = None
        start = ts[0][0]
        for t in ts:
            if t[1] >= eq.idle_threshold:
                cur_reason = available_reasons[0]
            else:
                cur_reason = available_reasons[1]

            # Do not forget to apply timetables

            if prev_reason is not None and (cur_reason.id != prev_reason.id or t[0] == ts[-1][0]):
                print('adding interval {0} {1} {2}'.format(start, t[0], cur_reason))
                try:
                    ClassifiedInterval.add_interval(start=start, end=t[0], equipment=eq, classification=prev_reason)
                except Exception as e:
                    print(e)
                    return
                prev_reason = cur_reason
                start = t[0]
            else:
                prev_reason = cur_reason
