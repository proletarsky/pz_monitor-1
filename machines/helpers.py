def prepare_data_for_google_charts_bar(data):
    charts_data = {}
    for key in data.keys():
        chart = data[key]['auto_stats']
        legend = ['Kind']
        graph_data = [key]
        for k in chart.keys():
            legend += [k]
            graph_data += [chart[k]]
        legend += [{'role': 'annotation'}]
        graph_data += ['']
        charts_data[key] = {'data': [legend, graph_data]}
    return charts_data
