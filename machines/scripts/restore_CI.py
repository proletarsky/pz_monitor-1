from machines.models import ClassifiedInterval, Reason
from django.contrib.auth.models import User
import psycopg2 as ps

HOST = 'localhos'
DB = 'moncopy'
USER = 'djangouser'
PWD = 'password'

cmd = 'select ci.start, ci.equipment_id, ci.automated_classification_id, ci.equipment_id, ci.user_id '\
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
        cis = ClassifiedInterval.objects().filter(equipment__id=eq_id,
                                                 automated_classification_id=auto_cl,
                                                 start__eq=start,
                                                 end__eq=end)
        if cis:
            user_reason = Reason.objects.get(id=user_id)
            user = User.objects.get(id=user_id)
            for ci in cis:
                ci.user_classification = user_reason
                ci.user = user
                ci.save()
        else:
            print(f'Interval {start}-{end} for equipment {eq_id} not found!')

if __name__ == '__main__':
    main()