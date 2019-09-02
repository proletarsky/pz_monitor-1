from machines.models import ClassifiedInterval, Reason
from django.contrib.auth.models import User
import psycopg2 as ps
from datetime import timedelta

HOST = '192.168.7.75'
DB = 'moncopy'
USER = 'djangouser'
PWD = 'password'

cmd = 'select ci.start, ci.end, ci.automated_classification_id, ci.equipment_id, ci.user_id '\
        'from machines_classifiedinterval ci where ci.user_classification_id is not null'


def main():
    print('Restore ClassifiedIntervals user data')

    conn = ps.connect(host=HOST, database=DB, user=USER, password=PWD)
    c = conn.cursor()
    c.execute(cmd)
    qs = c.fetchall()
    print('fetched {0} rows'.format(len(qs)))

    for data in qs:
        start, end, auto_cl, eq_id, user_id = data
        print(start, type(start))
        start_st = start - timedelta(minutes=2)
        start_en = start + timedelta(minutes=2)
        end_st = end - timedelta(minutes=2)
        end_en = end + timedelta(minutes=2)
        cis = ClassifiedInterval.objects.filter(equipment__id=eq_id,
                                                 automated_classification_id=auto_cl,
                                                 start__range = (start_st, start_en),
                                                 end__range=(end_st, end_en))
        if cis:
            user_reason = Reason.objects.get(id=user_id)
            user = User.objects.get(id=user_id)
            print(user)
            for ci in cis:
                ci.user_classification = user_reason
                ci.user = user
                ci.save()
        else:
            print('Interval {0}-{1} for equipment {2} not found!'.format(start, end, eq_id))

if __name__ == '__main__':
    main()