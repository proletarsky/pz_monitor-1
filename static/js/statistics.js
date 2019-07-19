var graphicsData = null;

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

    $("#id_periods_selector").change(function (e) {
        // console.log('select changed!');
        var cur_val = $(this).val();
        // console.log($(this).val());
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
    // console.log(graphicsData.total.data);
    var data = google.visualization.arrayToDataTable(graphicsData.total.data);

    var options = {
        width: '100%',
        height: '100%',
        legend: {position: 'top', maxLines: 3},
        chartArea: { width: '80%', height:'80%'},
        bar: { groupWidth: '30%' },
        isStacked: 'percent'
    };
    var chart = new google.visualization.BarChart(document.getElementById("id-plant"));
    chart.draw(data, options);
}

