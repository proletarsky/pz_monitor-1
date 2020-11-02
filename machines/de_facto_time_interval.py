import datetime
from .chill_calendar import  chill_days

# Функция для определения времени по факту с учетом 9 часового рабочего дня

def get_de_facto_time(start_date, end_date, start_time, end_time):
    # Начало рабочего дня
    work_start = datetime.timedelta(hours=7, minutes=0)
    # Конец рабочего дня
    work_end = datetime.timedelta(hours=16, minutes=0)

    # Если интервал по времени отрицательный, то старт ставим равный концу рабочего дня
    if (work_end - datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)).total_seconds() < 0:
        start_time = datetime.time(16, 00)
    # Аналогично для конца
    if (datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) - work_start).total_seconds() < 0:
        end_time = datetime.time(7, 00)

    # Если старт наступил до начала рабочего дня, то ставим его равным началу рабочего дня
    if datetime.timedelta(hours=start_time.hour, minutes=start_time.minute) < work_start:
        start_time = datetime.time(7, 00)
    # Аналогично для финиша
    if datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) > work_end:
        end_time = datetime.time(16, 00)

    if start_date > end_date:
        return timedelta(days=0,hours=0,minutes=0)

    # Если интервал начался и закончился в один и тот же день
    if start_date == end_date:
        # То высчитываем разницу во времени
        delta = datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) - \
                datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)
        # Если разница больше 0
        if delta > datetime.timedelta(hours=0, minutes=0):
            # Если меньшге 9 часов то возвращаем
            return delta if delta < datetime.timedelta(hours=9, minutes=0) \
                else datetime.timedelta(days=1,hours=0, minutes=0)
        else:
            return datetime.timedelta(hours=0)

    # Если между интервалами есть разница во времени
    if start_date < end_date:
        # Получаем все дни по календарю
        all_days = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        # Если интервал заканчивается на следующий день
        if len(all_days) == 2:
            # Считаем дни
            de_facto_days = ((work_end - datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)) + \
                             (datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) - \
                              work_start)) // datetime.timedelta(hours=9, minutes=0)
            # Часы с минутами
            de_facto_ours = ((work_end - datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)) + \
                             (datetime.timedelta(hours=end_time.hour,
                                                 minutes=end_time.minute) - work_start)) % datetime.timedelta(hours=9,
                                                                                                              minutes=0)
            de_facto = datetime.timedelta(days=de_facto_days) + de_facto_ours

            return de_facto if de_facto.days < len(all_days) +1  else datetime.timedelta(days=len(all_days)+1 )

        else:
            #Получаем все дни по календарю
            all_days = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
            #Получаем количество рабочих дней с учетом календаря
            work_days=len(sorted(list(set(all_days) - set(chill_days))))
            # Если дней больше одого, то высчитываем количество часов в промежутке между крайними днями
            hour_count = (work_days - 2) * 9
            de_facto_days = (datetime.timedelta(hours=hour_count, minutes=0) + \
                             (work_end - datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)) + \
                             (datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) - \
                              work_start)) // datetime.timedelta(hours=9, minutes=0)
            de_facto_ours = (datetime.timedelta(hours=hour_count, minutes=0) + \
                             (work_end - datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)) + \
                             (datetime.timedelta(hours=end_time.hour, minutes=end_time.minute) - \
                              work_start)) % datetime.timedelta(hours=9, minutes=0)
            de_facto = datetime.timedelta(days=de_facto_days) + de_facto_ours
            return de_facto if de_facto.days < work_days +1  else datetime.timedelta(days=work_days+1 )
