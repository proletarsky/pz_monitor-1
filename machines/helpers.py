import requests
from django.conf import settings

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
def SendSMS(phone, message):
    # *************************************************
    """!!!Формирование текста СМС и номеров получателей!!!"""
    assert isinstance(phone, int) and str(phone)[0] == '7', 'phone must be NUMBER and starts with 7'
    # кому отправлять СМС
    # phone = 7...

    # текст СМС
    # newPass = "Qwer1234"  # для записи переменных данных
    # msg = "ваш новый пароль к системе мониторинга "  + newPass
    # msg = "тестовое СМС для системы мониторинга"
    # *************************************************

    # тело запроса
    sms = {
        "from": "PZMONITOR",
        "to": phone,
        "message": message
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
