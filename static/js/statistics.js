var graphicsData = null;
var colorsJSON = null;

$(document).ready(function () {

    $('#id_start_date').datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: "yy-mm-dd"
    });

    $('#id_end_date').datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: "yy-mm-dd"
    });

    // $('#id_periods_selector').val('прошлая декада');
    // set_period('прошлая декада');
    if (graphicsData !== null)
        console.log(graphicsData);
    else
        console.log('No Data');

    $("#id_periods_selector").change(function (e) {
        console.log('select changed!');
        var cur_val = $(this).val();
        console.log($(this).val());
        set_period(cur_val);
   });

    $('#show-hide-plant').click(function (e) {
        e.preventDefault();
        $('.toggled-pane-total').toggle('slow');
        var txt = $('#show-hide-plant').text();
        if (txt === 'Показать')
            txt = 'Скрыть';
        else
            txt = 'Показать';
        // console.log(txt);
        $('#show-hide-plant').text(txt);
    });

    var ids = "";
    var keys = Object.keys(graphicsData);
    for(var i = 1; i <= keys.length; i++){
        if (keys[i-1] !== 'total')
            ids += (ids.length === 0 ? '' : ',') + `#show-hide-${i}`;
    }
    $(ids).click(function (e) {
        e.preventDefault();
        var elementID = $(this).attr('id');
        var id = elementID.split('-').pop();
        var classID = `.toggled-pane-${id}`;
        // console.log(`elID = ${elementID}`);
        $(classID).toggle('slow');
        var txt = $(`#${elementID}`).text();
        if (txt === 'Показать')
            txt = 'Скрыть';
        else
            txt = 'Показать';
        $(`#${elementID}`).text(txt);
    })
});

function formatDate(date) {
    var month = (date.getMonth() + 1).toString().padStart(2, '0');
    var day = date.getDate().toString().padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
}

function set_period(period) {
        switch (period) {
           case 'прошлая неделя':
               var date = new Date();
               var dayOfWeek = date.getDay();
               var endPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() - dayOfWeek + 1);
               var startPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() - dayOfWeek - 6);
               $('#id_start_date').val(formatDate(startPeriod));
               $('#id_end_date').val(formatDate(endPeriod));
               $('#id_start_date').attr('readonly', true);
               $('#id_end_date').attr('readonly', true);
               break;
           case 'прошлая декада':
               var date = new Date();
               var extra = date.getDate() % 10;
               var endPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1 - extra);
               var startPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() - 9 - extra);
               $('#id_start_date').val(formatDate(startPeriod));
               $('#id_end_date').val(formatDate(endPeriod));
               $('#id_start_date').attr('readonly', true);
               $('#id_end_date').attr('readonly', true);
               break;
           case 'прошлый месяц':
               var date = new Date();
               var endPeriod = new Date(date.getFullYear(), date.getMonth(), 1);
               var startPeriod = new Date(date.getFullYear(), date.getMonth()-1, 1);
               $('#id_start_date').val(formatDate(startPeriod));
               $('#id_end_date').val(formatDate(endPeriod));
               $('#id_start_date').attr('readonly', true);
               $('#id_end_date').attr('readonly', true);
               break;
           case 'текущий месяц':
               var date = new Date();
               var endPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1);
               var startPeriod = new Date(date.getFullYear(), date.getMonth(), 1);
               $('#id_start_date').val(formatDate(startPeriod));
               $('#id_end_date').val(formatDate(endPeriod));
               $('#id_start_date').attr('readonly', true);
               $('#id_end_date').attr('readonly', true);
               break;
           default:
               $('#id_start_date').attr('readonly', false);
               $('#id_end_date').attr('readonly', false);
               break;
       }
}

// Google charts
google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);
function drawChart() {
    var auto_data = google.visualization.arrayToDataTable(graphicsData.total.auto_data);
    var user_data = google.visualization.arrayToDataTable(graphicsData.total.user_data);
    var data_keys = Object.keys(graphicsData.details);


    var eq_auto_data = [];
    var eq_user_data = [];
    for (var i = 1; i <= data_keys.length; i++){
        var eq_auto = google.visualization.arrayToDataTable(graphicsData.details[data_keys[i-1]].auto_data);
        var eq_user = google.visualization.arrayToDataTable(graphicsData.details[data_keys[i-1]].user_data);
        //console.log(eq_user)
        eq_auto_data.push(eq_auto);
        eq_user_data.push(eq_user);
    }


    var options_auto = {
        width: '100%',
        height: '100%',
        legend: {position: 'top', maxLines: 3},
        chartArea: { width: '80%', height:'80%'},
        bar: { groupWidth: '30%' },
        isStacked: 'percent'
    };
    var list_color_total=[]

    var new_total_array_data=[]
    graphicsData.valueOf().total.user_data.forEach(x=>new_total_array_data.push(x[0]))
    var new_total_array_data_filter_ON=[]
    new_total_array_data_filter_ON=new_total_array_data.filter(x=>x!='user_reason')

    var color_reason_list=[]
    colorsJSON.valueOf().forEach(x=>color_reason_list.push(x.description))



    //Функция для определения цвета по наименованию причины простоя
    function color_def(searched_color) {
        var ind=color_reason_list.indexOf(searched_color)
        if(ind==-1){
            return "#C0C0C0"
        }
        else {
            return colorsJSON[ind].color
        }
    }

    new_total_array_data_filter_ON.forEach(x=>list_color_total.push(color_def(x)))

    var options_user_total = {
        width: '100%',
        height: '100%',
        pieHole: 0.4,
        colors:list_color_total
    };

    var auto_data_chart = new google.visualization.BarChart(document.getElementById("id-plant"));
    var user_data_chart = new google.visualization.PieChart(document.getElementById("id-plant-userdata"));
    auto_data_chart.draw(auto_data, options_auto);
    user_data_chart.draw(user_data, options_user_total);



    for (var i = 1; i <= data_keys.length; i++){
        var auto_chart = new google.visualization.BarChart(document.getElementById(`id-work-${i}`));
        var user_chart = new google.visualization.PieChart(document.getElementById(`id-userdata-${i}`));

        var list_color_example=[]

        var machine_new_array_data=[]
        Object.values(graphicsData.details)[i-1].user_data.forEach(x=>machine_new_array_data.push(x[0]))
        var machine_new_array_data_filter_ON=machine_new_array_data.filter(x=>x!='user_reason')

        machine_new_array_data_filter_ON.forEach(x=>list_color_example.push(color_def(x)))


        var options_user_example = {
            width: '100%',
            height: '100%',
            pieHole: 0.4,
            colors:list_color_example

        };
        auto_chart.draw(eq_auto_data[i-1], options_auto);
        user_chart.draw(eq_user_data[i-1], options_user_example);


    }
}

