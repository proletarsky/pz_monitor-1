def prepare_data_for_google_charts_bar(data):
    charts_data = {}
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
        charts_data[key] = {'auto_data': [legend, graph_data], 'user_data': user_data}
    return charts_data
