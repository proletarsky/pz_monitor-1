from machines.models import RawData
from django.utils import timezone
import psycopg2 as ps
import sys, re, datetime

HOST = '192.168.7.75'
DB = 'pzmonitor'
USER = 'djangouser'
PWD = 'password'


def main():
    try:
        print('Ask RawData for {:%Y-%m-%d}'.format(timezone.now()))
        conn = ps.connect(host=HOST, database=DB, user=USER, password=PWD)
        c = conn.cursor()
        sql_cmd = "select * from machines_rawdata where date > '{:%Y-%m-%d}'".format(timezone.now())
        c.execute(sql_cmd)
        qs = c.fetchall()
        print('fetched %d rows' % len(qs))
        for data in qs:
            row = RawData(date=data[1], mac_address=data[2], value=data[3], channel=data[4], ip=data[5])
            row.save()
        print('added %d rows' % len(qs))
    except Exception as e:
        print(e)
        usage()
    finally:
        if conn is not None:
            conn.close()


def usage():
    print("Usage: manage.py get_raw_data_from_server")
    print('it loads data for today')
    sys.exit(1)


if __name__ == '__main__':
    main()
