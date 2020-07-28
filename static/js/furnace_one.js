$(document).ready(function () { 

    $(".datepicker").change(function (e) {
        var txt = $('#btn_save_and_go').val();
        //console.log(txt);
        if (txt.includes("Сохранить")) {
            //console.log("User has rights");
            $('#btn_save_and_go').val("Сохранить и перейти");
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
//dataarray.push(normdate(googlecharts_data_track[i][0]),googlecharts_data_track[i][1]);
dataarray.push(googlecharts_data_track.length[i]);
}


// ТУТ БЫЛО
google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(drawChart1);
function drawChart1() {
    var data = new google.visualization.DataTable();
//    var data = new google.visualization.arrayToDataTable(data);

  data.addColumn('number', 'Время');
  data.addColumn('number', 'Значение');
  var y = 50;


//data.addRow(googlecharts_data_track);


  for (var i = 0; i < 100; i++) {
        y += Math.ceil(Math.random() * 3) * Math.pow(-1, Math.floor(Math.random() * 2));
        data.addRow([i, y]);
    }




    var chart = new google.visualization.LineChart(document.getElementById('test_charts'));
    chart.draw(data, {
        width:'100%',
        height:500,
        explorer: {
            axis: 'horizontal',
            keepInBounds: true,
            maxZoomIn: 0.1,
            maxZoomOut: 1

        },
//vAxis: {maxValue: 1500},

 /*axisTitlesPosition: 'out',
        'isStacked': true,*/
/*chartArea: {
            left: "0",
            top: "0",
            height: "80%",
            width: "90%"
        },*/
        hAxis: {
            viewWindow: {
                max: '100%',
                min: '100%'
            }
        }
    });
}

$(window).on("throttledresize", function (event) {
    drawChart1();
});

var currentMin = '100%';
var currentMax = '100%';


google.setOnLoadCallback(function() {
    $("#LButton").click(function () {
        currentMax -= '10%';
        currentMin -= '10%';
        drawChart1();
    });
    $("#RButton").click(function () {
      	currentMax += '10%';
        currentMin += '10%';
        drawChart1();
    });
});

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


$(window).resize(function(){drawChart1();});


google.load('visualization', '1', {
    packages: ['corechart'],
    callback: drawChart1
});

});