import requests
from django.conf import settings
import re

def prepare_data_for_google_charts_bar(data):
    charts_data = {}
    charts_data['details'] = {}
    for key in data.keys():
        chart = data[key]['auto_stats']
        chart2 = data[key]['user_stats']
        legend = ['Kind']
        graph_data = [key]
        user_data = [['user_reason', 'min']]
        for k in chart.keys():
            legend += [k]
            graph_data += [chart[k]]
        for k in chart2.keys():
            user_data += [[k, chart2[k]]]
        legend += [{'role': 'annotation'}]
        graph_data += ['']
        if key == 'total':
            charts_data[key] = {'auto_data': [legend, graph_data], 'user_data': user_data}
        else:
            charts_data['details'][key] = {'auto_data': [legend, graph_data], 'user_data': user_data}
    return charts_data


# api_URL = "https://a2p-api.megalabs.ru/sms/v1/sms"
# кодируем связку логин:пароль
# usrPass = "NW_prtzvd:K63GG1ag"
# b64Val = base64.b64encode(usrPass.encode("ascii")).decode("ascii")
def SendSMS(phone, pattern, message):
    """
    sends SMS to number 'phone'
    :param phone: string +7(912)3492849
    :param message:
    :return: Http code
    """
    # *************************************************
    """!!!Формирование текста СМС и номеров получателей!!!"""
    ph = re.sub(r'([-\s\+\(\)]*)', "", phone)
    assert (ph)[:2] == '79', 'phone should start with 79'
    try:
        ph = int(ph)
    except ValueError as e:
        raise ValueError("invalid phone number {0}".format(phone))
    assert isinstance(pattern, int) and pattern >= 0 and pattern < len(settings.SMS_PATTERNS), "invalid pattern"

    # кому отправлять СМС
    # phone = 7...

    # текст СМС
    # newPass = "Qwer1234"  # для записи переменных данных
    # msg = "ваш новый пароль к системе мониторинга "  + newPass
    # msg = "тестовое СМС для системы мониторинга"
    # *************************************************

    if re.search(r'\{\d\}', settings.SMS_PATTERNS[pattern]):
        msg = settings.SMS_PATTERNS[pattern].format(message)
    else:
        msg = settings.SMS_PATTERNS[pattern]

    # тело запроса
    sms = {
        "from": "PZMONITOR",
        "to": ph,
        "message": msg
    }

    # заголовок
    head = {
        "Authorization": "Basic %s" % settings.SMS_PASS_PHRASE
    }

    # отправка запроса
    r = requests.post(settings.SMS_API_URL, headers=head, json=sms)

    # статус и отчет о выполнении, не обязательно
    print(r.status_code)
    print(r.text)

    return r.status_code
