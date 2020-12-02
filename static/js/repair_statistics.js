var graphicsData = null;
var colorsJSON = null;

$(document).ready(function () {
/*
var urlParams = new URLSearchParams(window.location.search);

if(urlParams.toString()==''){
set_period('прошлая неделя');
urlParams.append('start_date', $('#id_start_date').val());
urlParams.append('end_date', $('#id_end_date').val());
location.hash = urlParams.toString();
}
*/

/*
  $('.dates').each(function( index ) {    
    var text = $(this).text(),splArr = text.split(','),newtext='';
    console.log(splArr[0]);
   if(splArr[0] && splArr[0]!=''){
     var newsplArr = splArr[0].split(' ');
     newsplArr = newsplArr[0].slice(-1);
     var newday = '';
     if(newsplArr=='1'){newday = 'день';}
     if(newsplArr=='2' || newsplArr=='3' || newsplArr=='4'){newday = 'дня';}
     if(newsplArr=='0' || newsplArr=='5' || newsplArr=='6' || newsplArr=='7' || newsplArr=='8' || newsplArr=='9'){newday = 'дней';}
     if(splArr[1] && splArr[1]!=''){
     $(this).text(splArr[0]+' '+newday+splArr[1]);
   }
   }
});
*/

$("#id_empty_only").on('change', function() {
  if ($(this).is(':checked')) {
    $(this).attr('value', 'True');
  } else {
    $(this).attr('value', 'False');
  }
  
  //$('#checkbox-value').text($('#checkbox1').val());
});

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



$('.show-hide-button').click(function (e) {
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




var fform = $('.act-form');
//if(fform.data('area_id')){$('#area_id_param').val(fform.data('area_id'));}
if(fform.data('start')){$('#id_start_date').val(fform.data('start'));}
if(fform.data('end')){$('#id_end_date').val(fform.data('end'));}
if( fform.data('bool') && fform.data('bool')=='True' ){$('#id_empty_only').prop("checked", true);}
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


