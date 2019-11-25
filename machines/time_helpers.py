from django.utils import timezone
from django.conf import settings
import datetime
import pandas as pd
import re


class CurrentDayType(object):
    day_type = None
    updated = None

    @staticmethod
    def get_day_type():
        if (CurrentDayType.day_type is not None
                and CurrentDayType.updated is not None
                and CurrentDayType.get_working_day(CurrentDayType.updated) ==
                CurrentDayType.get_working_day(timezone.localtime().day)):
            return CurrentDayType.day_type

        date = timezone.localtime()
        df = pd.read_csv('machines/holidays.csv', index_col=[0])
        days = df.loc[date.year, df.columns[date.month - 1]].split(',')
        holidays = [int(d) for d in days if re.match(r'^\d+$', d)]
        preholidays = [int(d[:-1]) for d in days if re.match(r'^\d+\*$', d)]
        if date.day in holidays:
            CurrentDayType.day_type = 1  # holiday
        elif date.day in preholidays:
            CurrentDayType.day_type = 2  # eve holiday (pre holiday)
        else:
            CurrentDayType.day_type = 0  # working day
        CurrentDayType.updated = date
        return CurrentDayType.day_type

    @staticmethod
    def get_working_day(date: datetime.datetime):
        return (date.day if date.hour * 3600 + date.minute * 60 + date.second >=
                            settings.START_TIME_DAY.hour * 3600 + settings.START_TIME_DAY.minute * 60
                            + settings.START_TIME_DAY.second
                else (date + datetime.timedelta(days=-1)).day)


def get_duration_minutes(start: datetime.time, end: datetime.time):
    duration = (end.minute - start.minute) + (end.hour - start.hour) * 60
    return duration if duration > 0 else 1440 + duration

