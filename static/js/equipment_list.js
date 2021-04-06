var graphicsData = null;
$(document).ready(function () {
   console.log(JSON.stringify(graphicsData));
   console.log(Date.parse('2019-08-08T12:12:13'));
   console.log(JSON.parse(JSON.stringify(graphicsData), JSON.dateParser));

var urlParams = new URLSearchParams(window.location.search);
if(urlParams.toString()!=''){
if(urlParams.has('workshop')){
var exists = 0 != $('#id_workshop option[value='+parseInt(urlParams.get('workshop'))+']').length;
if(exists){$('#id_workshop').val(parseInt(urlParams.get('workshop')));}
}

if(urlParams.has('area')){
var exists = 0 != $('#id_area option[value='+parseInt(urlParams.get('area'))+']').length;
if(exists){$('#id_area').val(parseInt(urlParams.get('area')));}
}

if(urlParams.has('machine_or_furnace_sign')){
$('#type_workshop').val( urlParams.get('machine_or_furnace_sign') );
$('#type_w').val( urlParams.get('machine_or_furnace_sign') )
}

if(urlParams.has('model')){
$('#id_model').val(urlParams.get('model'));
}
//location.hash = urlParams.toString();
}



if($('table>tbody>tr').length==0){
$('table').after('<div class="no-result"><h2>По данному запросу ничего не найдено.</h2></div>');
}

});

function getDatetime(str){
    console.log(str);
    console.log(typeof str);
    // console.log(str.match(/(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d:{1,2)/));
    if (typeof str === 'object'){
        return str.map(s=>getDatetime(s));
    }
    else if (typeof str === 'string' && str.match()) {
        let parsed = str.match(/(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d:{1,2)/).slice(1).map(i => parseInt(i));
        return new Date(parsed[0], parsed[1] - 1, parsed[2], parsed[3], parsed[4], parsed[5]);
    }
    else {
        return str;
    }
}

$(document.body).on('change',"#type_workshop",function (e){
   var optVal= $("#type_workshop option:selected").val();
   if($('#type_w').val()!=optVal){
   $('#type_w').val(optVal);
   $('#sendform').click();
   }
});

function dateParser(value) {
    let reISO = /(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})/;
    // console.log(value);
    // console.log(typeof value);
    // console.log(reISO.exec(value));
    if (typeof value === 'string' && reISO.exec(value)) {
            return new Date(value);
    }
    else {
        try {
            let classID = parseInt(value);
            switch (classID) {
                case 999:
                    return 'yellow';
                case 0:
                    return 'green';
                case 1:
                    return 'red';
                default:
                    return value;
            }
        }
        catch (e) {
            return value;
        }
    }
        return value;
};
function arrayParser(arr) {
    let newArr = [];
    arr.forEach(function (obj, i, array) {
        newArr.push(obj.map(x=>dateParser(x)));
    });
    console.log(newArr);
    return newArr;
}

// Google charts
  function loadTheMap() {
    google.load("visualization", "1", {packages:["timeline"]});
    console.log('Callback is set');
  }

 // setTimeout(loadTheMap, 200);

google.load("visualization", "1", {packages:["timeline"]});
google.setOnLoadCallback(drawChart);
function drawChart() {
    // console.log(graphicsData.total.data);
    let data_keys = Object.keys(graphicsData);
    // console.log(data_keys);
    let eq_auto_data = [];
    let eq_ids = [];
    data_keys.forEach(function (val, ind, arr) {
        let eq_auto = new google.visualization.DataTable();
        eq_auto.addColumn({ type: 'string', id: 'Role' });
        eq_auto.addColumn({ type: 'string', id: 'Name' });
        eq_auto.addColumn({type: 'string', id: 'style', role: 'style'}),
        eq_auto.addColumn({ type: 'date', id: 'Start' });
        eq_auto.addColumn({ type: 'date', id: 'End' });
        console.log('Try add row');
        graphicsData[val].forEach(function (row, i, array) {
            // let row_data =
            eq_auto.addRow(row.map(v=>dateParser(v)));
        });
        console.log(eq_auto);
        eq_auto_data.push(eq_auto);
        eq_ids.push(val);
    });

    let options_auto = {
        // colors: ['green', 'red', 'yellow'],
        timeline: {
            showRowLabels: false,
            showBarLabels: false
        },
        // width: '100%',
        //height: '20',
        // chartArea: { width: '100%', height:'80%'},
        hAxis: {
            format: "HH:mm"
        }
    };


console.log('DATA!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
console.log(eq_auto_data);
console.log('DATA!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'+eq_ids);

function afterDraw(x){
    console.log('all done '+x);
$('#graph-'+x).removeClass('equip-loading');
}

eq_auto_data.forEach(function (val, i, arr) {

//console.log(val);
//console.log(arr);
if ($('#graph-'+eq_ids[i]).length > 0) {
       let chart = new google.visualization.Timeline(document.getElementById(`graph-${eq_ids[i]}`));
       google.visualization.events.addListener(chart, 'ready', function(){
$('#graph-'+eq_ids[i]).removeClass('equip-loading');

});
       chart.draw( eq_auto_data[i], options_auto);
    }else{console.log('НЕТ ТАКОГО НА СТРАНИЦЕ!!!!!!!!!____'+i);}
    });


}
