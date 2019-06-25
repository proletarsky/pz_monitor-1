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
});