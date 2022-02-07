import datetime

from machines.models import Equipment, Workshop, ClassifiedInterval
from django.utils import dateparse

# Get data for the past week
def get_previous_week_report():
    today = datetime.datetime.now()
    start_delta = datetime.timedelta(days=datetime.datetime.today().weekday(), weeks=1)

    start_date = (today - start_delta).strftime("%Y-%m-%d")
    end_date = (today - start_delta + datetime.timedelta(days=6)).strftime("%Y-%m-%d")

    workshop_id = [x.workshop_number for x in Workshop.objects.all()]

    problem_machines = [x.id for x in Equipment.objects.filter(problem_machine=True, is_in_monitoring=True,
                                                               workshop_id__in=workshop_id)]

    stat_data = {}

    problem_stat_data = {}

    if start_date is not None and start_date != '' and end_date is not None and end_date != '':
        stat_data = ClassifiedInterval.get_report_data(start_date, end_date, workshop_id=workshop_id)

        problem_stat_data = Equipment.report_problem_statistics(start_date, end_date, workshop_id=workshop_id,
                                                                equipment=problem_machines)

    joined_report = stat_data['day_stats'] + problem_stat_data['day_stats']

    # Delete test machines
    for i in range(len(joined_report)):
        if joined_report[i]['code'] == "TEST":
            del joined_report[i]
            break

    total_keys_list = {**problem_stat_data['total_workshop_user_data'], **stat_data['total_workshop_user_data']}

    dict_to_sorting = {
        7: 1,
        8: 2,
        26: 3,
        14: 4,
        9: 5,
        20: 6,
        1: 7
    }

    if stat_data and problem_stat_data:
        for key, value in total_keys_list.items():
            t_dict = {}

            if key in stat_data['total_workshop_user_data'] and key in problem_stat_data[
                'total_workshop_user_data'] and bool(problem_stat_data['total_workshop_user_data'][key]) and bool(
                    stat_data['total_workshop_user_data'][key]):
                total_keys_list[key] = [value, problem_stat_data['total_workshop_user_data'][key]]
                for item in total_keys_list[key]:
                    for atom_key, atom_value in item.items():
                        if atom_key in t_dict:
                            t_dict[atom_key] += atom_value
                        else:
                            t_dict[atom_key] = atom_value
                    total_keys_list[key] = t_dict
            else:
                total_keys_list[key] = value

    total_user_stats = []

    for workshop, reason in total_keys_list.items():
        user_stats_value = [sum(reason.values())]
        if reason:
            for k, v in reason.items():
                if k == '000 - Не указано':
                    total_user_stats.append({
                        'workshop_id': workshop,
                        'workshop_user_stats': round(v / max(user_stats_value) * 100, 1)
                    })
        else:
            total_user_stats.append({
                'workshop_id': workshop,
                'workshop_user_stats': 0
            })

    workshop_sort_joined_report = sorted(total_user_stats, key=lambda k: dict_to_sorting[k['workshop_id']])

    previous_week_data = {
        'workshop_sort_joined_report': workshop_sort_joined_report,
        'previous_week_start_date': dateparse.parse_date(start_date),
        'previous_week_end_date': dateparse.parse_date(end_date)
    }
    return previous_week_data


# Временные данные до уточнения статуса оборудования
# fake_data = [{
#     'workshop_id': 8,
#     'code': 'СШО №5',
#     'model': 'Печь',
#     'days_percent': ['нет данных']*(delta.days+1),
#     'total_percent': 0,
#     'user_stats': [('666 - Технические работы системы мониторинга', 100)]
# }, {
#     'workshop_id': 8,
#     'code': '001',
#     'model': 'Пресс LKM 1600',
#     'days_percent': ['нет данных']*(delta.days+1),
#     'total_percent': 0,
#     'user_stats': [('666 - Технические работы системы мониторинга', 100)]
# }, {
#     'workshop_id': 26,
#     'code': '30684',
#     'model': '6625У',
#     'days_percent': ['нет данных']*(delta.days+1),
#     'total_percent': 0,
#     'user_stats': [('666 - Технические работы системы мониторинга', 100)]
# }]