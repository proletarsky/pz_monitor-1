$(document).ready(function () { /*
    var d = new Date();
    var day = d.getDate();
    var month = d.getMonth() + 1;
    var year = d.getFullYear();
    var today = document.getElementById('mycalendar')
    if (month<10){
        today.value = year + "-" + "0" + month + "-" + day;
    }
    else {
        today.value = year + "-" + month + "-" + day;
    }
    
    $('#mycalendar').change(function (e) {
        var btn = $('#btn_save_and_go');
        if (btn.is('visible')) { // It means that user has rights to change form
            var date = $('#mycalendar').val();
            var now = new Date().toISOString();
            if (now.includes(date))
                $('#btn_save_and_go').val("Сохранить");
            else
                $('#btn_save_and_go').val("Сохранить и перейти");
        }
        else {
            var url = window.location.href;
            var date = $('#mycalendar').val();
            console.log(url);
            window.locataion = url + "?date=" + date;
        }
    })*/

var olddate= $(".datepicker").val();

$.date = function(dateObject) {
    var d = new Date(dateObject);
    var day = d.getDate();
    var month = d.getMonth() + 1;
    var year = d.getFullYear();
    if (day < 10) {
        day = "0" + day;
    }
    if (month < 10) {
        month = "0" + month;
    }
    var date = day + "/" + month + "/" + year;

    return date;
};


    $(".datepicker").change(function (e) {
        var txt = $('#btn_save_and_go').val();
        //console.log(txt);
        if (txt.includes("Сохранить")) {
            //console.log("User has rights");
            $('#btn_save_and_go').val("перейти");
        }
    });

    $(".datepicker").datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: "yy-mm-dd"
    })
    //$(".datepicker").type="date";


//explorer: {maxZoomOut:2,keepInBounds: true}

var dataarray = [];
dataarray.push(['Время', 'Значение']);
for(var i=0;i<googlecharts_data_track.length;i++){
dataarray.push(googlecharts_data_track[i]);
}

/*
google.setOnLoadCallback(function() {
    $("#LButton").click(function () {
        currentMax -= '10%';
        currentMin -= '10%';
        drawChart();
    });
    $("#RButton").click(function () {
      	currentMax += '10%';
        currentMin += '10%';
        drawChart();
    });
});
*/
$('.ciselect').on('change', function() {
  $('.ui-datepicker-trigger').remove();
  $('#id_date').val(olddate).prop('readonly', true);
  $('#btn_save_and_go').val("Сохранить");
});

$(window).resize(function(){drawChart();});


 google.charts.load('current', {
        'packages': ['corechart']
      });
      google.charts.setOnLoadCallback(drawChart);

console.log('111111');
console.log(googlecharts_data_track);
console.log('111111');

var result = [];
for (var i=0; i<googlecharts_data_track.length-1;i++){
//console.log(googlecharts_data_track[i][0].toJSON().replace(/-/g,'/'));

if ( isNaN( googlecharts_data_track[i][0].getTime() ) ) {
if(i>0){
if ( !isNaN( googlecharts_data_track[i-1][0].getTime() ) ) {
googlecharts_data_track[i][0] = new Date(googlecharts_data_track[i-1][0].getTime() + 3600);
//console.log(googlecharts_data_track[i]);
}

}
//googlecharts_data_track[i][0].toJSON().replace(/-/g,'/');
//googlecharts_data_track[i][0].replace(/-/g,'/');
//googlecharts_data_track[i][0] = new Date(googlecharts_data_track[i][0]).toDateString();
}
result.push( googlecharts_data_track[i] );
}

console.log(googlecharts_data_track);

      function drawChart() {
//        var data = new google.visualization.arrayDataTable();
	var data = new google.visualization.DataTable();
  data.addColumn('date', 'Время');
  data.addColumn('number', 'Значение');
//data.addColumn ('string', 'Date');
//data.addColumn ('number', 'Users');
data.addRows(result);

/*	  [
          ['Период', 'Температура'],
          [new Date(2001, 01, 01), 30],
          [new Date(2002, 01, 01), 70],
          [new Date(2003, 01, 01), 45],
          [new Date(2004, 01, 01), 99],
          [new Date(2005, 01, 01), 22],
          [new Date(2006, 01, 01), 0],
          [new Date(2007, 01, 01), 89],
          [new Date(2008, 01, 01), 30],
          [new Date(2009, 01, 01), 32],
          [new Date(2010, 01, 01), 77],
          [new Date(2011, 01, 01), 67],
          [new Date(2012, 01, 01), 22],
          [new Date(2013, 01, 01), 23],
          [new Date(2014, 01, 01), 25],
          [new Date(2015, 01, 01), 9],
          [new Date(2016, 01, 01), 10],
          [new Date(2017, 01, 01), 77],
          [new Date(2018, 01, 01), 47],
          [new Date(2019, 01, 01), 22],
          [new Date(2020, 01, 01), 23],
          [new Date(2022, 01, 01), 12],
          [new Date(2023, 01, 01), 9],
          [new Date(2024, 01, 01), 10],
          [new Date(2025, 01, 01), 10],
          [new Date(2026, 01, 01), 77],
          [new Date(2027, 01, 01), 67],
          [new Date(2028, 01, 01), 22],
          [new Date(2029, 01, 01), 23],
          [new Date(2030, 01, 01), 34],
          [new Date(2031, 01, 01), 9],
          [new Date(2032, 01, 01), 10],
          [new Date(2033, 01, 01), 22],
          [new Date(2034, 01, 01), 23],
          [new Date(2035, 01, 01), 19],
          [new Date(2036, 01, 01), 12],
          [new Date(2037, 01, 01), 10],
          [new Date(2038, 01, 01), 17],
          [new Date(2039, 01, 01), 6],
          [new Date(2040, 01, 01), 6],
          [new Date(2041, 01, 01), 22],
          [new Date(2042, 01, 01), 23],
          [new Date(2043, 01, 01), 71],
          [new Date(2044, 01, 01), 9],
          [new Date(2045, 01, 01), 10],
          [new Date(2046, 01, 01), 78],
          [new Date(2047, 01, 01), 67],
          [new Date(2048, 01, 01), 22],
          [new Date(2049, 01, 01), 23],
          [new Date(2050, 01, 01), 12],
          [new Date(2051, 01, 01), 13],
          [new Date(2052, 01, 01), 10],
          [new Date(2053, 01, 01), 77],
          [new Date(2054, 01, 01), 47],
          [new Date(2055, 01, 01), 22],
          [new Date(2056, 01, 01), 23],
          [new Date(2057, 01, 01), 12],
          [new Date(2058, 01, 01), 9],
          [new Date(2059, 01, 01), 10],
          [new Date(2060, 01, 01), 10],
          [new Date(2061, 01, 01), 76],
          [new Date(2062, 01, 01), 67],
          [new Date(2063, 01, 01), 22],
          [new Date(2064, 01, 01), 23],
          [new Date(2065, 01, 01), 34],
          [new Date(2066, 01, 01), 9],
          [new Date(2067, 01, 01), 10],
          [new Date(2068, 01, 01), 22],
          [new Date(2069, 01, 01), 23],
          [new Date(2070, 01, 01), 19],
          [new Date(2071, 01, 01), 12],
          [new Date(2072, 01, 01), 10],
          [new Date(2073, 01, 01), 17],
          [new Date(2074, 01, 01), 6],
          [new Date(2075, 01, 01), 6],
          [new Date(2076, 01, 01), 22],
          [new Date(2077, 01, 01), 23],
          [new Date(2078, 01, 01), 70],
          [new Date(2079, 01, 01), 9],
          [new Date(2080, 01, 01), 10],
          [new Date(2081, 01, 01), 72],
          [new Date(2082, 01, 01), 67],
          [new Date(2083, 01, 01), 22],
          [new Date(2084, 00, 04), 23],
          [new Date(2085, 01, 01), 12],
          [new Date(2086, 01, 01), 13]
	  ]
		

        ); */
var w = window.innerWidth
|| document.documentElement.clientWidth
|| document.body.clientWidth;

        var options = {
          title: 'Печь',
          hAxis: {
            title: 'Печь',
	   maxTextLines: 1,
            titleTextStyle: {
              color: '#333'
            },
          },
	  chartArea: {left: 40, top: 20, width: '85%', height: '100%'},
         /* vAxis: {
            minValue: 0
          },
*/
          explorer: {
            axis: 'horizontal',
            keepInBounds: true,
            maxZoomIn: 4.0
          },

          colors: ['#D44E41'],width: w,
        };

        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
      }


var w = window.innerWidth
|| document.documentElement.clientWidth
|| document.body.clientWidth;
    function printDiv(divName) {
     var printContents = document.getElementById(divName).innerHTML;
     var originalContents = document.body.innerHTML;

     document.body.innerHTML = printContents;

     window.print();

     document.body.innerHTML = originalContents;
}

$(document).on( "click", "#PRINT_BTN", function(chart){
printDiv('forprint');
});




});