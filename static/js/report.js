document.querySelectorAll(".report__table-header-cell-common").forEach(el => {
    if (el.innerHTML.slice(0, -1) >= 0 && el.innerHTML.slice(0, -1) <= 1) {
        el.style.backgroundColor = "#F8CBAD";
    } else if (el.innerHTML.slice(0, -1) > 0 && el.innerHTML.slice(0, -1) <= 32) {
        el.style.backgroundColor = "#FFF2CC";
    } else if (el.innerHTML.slice(0, -1) > 32) {
        el.style.backgroundColor = "#ffffff";
    }
});

document.querySelectorAll(".report__table-cell-no-reason").forEach(el => {
    if (el.innerText.slice(0, -1) >= 32) {
       el.style.color = "#ff0000"
    }
    el.style.fontWeight = "bold"
});

document.querySelectorAll(".report__table-total-reason").forEach(el => {
    if (el.innerHTML.includes('не указано')) {
        el.style.color = "#ff0000"
    }
});

document.querySelectorAll(".report__table-total-reason-list > span").forEach(el => {
    if (el.innerHTML.includes('Не указано')) {
        el.style.fontWeight = "bold"
    }
});

document.querySelectorAll(".report__table-cell").forEach(el => {
    if (el.innerHTML.includes('цех')) {
        el.style.fontWeight = "bold"
    }
});

document.querySelectorAll(".report__table-body-cell-info").forEach(el => {
    if (el.innerHTML.includes('%')) {
        el.style.fontWeight = "bold"
    }
});

document.querySelectorAll(".report__table-total-row > td").forEach(el => {
    if (el.colSpan > 1) {
        el.style.backgroundColor = "#999999"
    }
});

document.querySelectorAll(".report__table-header-days").forEach(el => {
    if (el.innerHTML.indexOf("Monday") === 0) {
        var re = /Monday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'ПН');
    } else if (el.innerHTML.indexOf("Tuesday") === 0) {
        var re = /Tuesday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'BT');
    } else if (el.innerHTML.indexOf("Wednesday") === 0) {
        var re = /Wednesday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'СР');
    } else if (el.innerHTML.indexOf("Thursday") === 0) {
        var re = /Thursday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'ЧТ');
    } else if (el.innerHTML.indexOf("Friday") === 0) {
        var re = /Friday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'ПТ');
    } else if (el.innerHTML.indexOf("Saturday") === 0) {
        var re = /Saturday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'СБ');
    } else if (el.innerHTML.indexOf("Sunday") === 0) {
        var re = /Sunday/gi;
        el.innerHTML = el.innerHTML.replace(re, 'ВС');
    }
});


// Function to merge cells
$(function () {
    $.map($(".report__workshop"), function (b, a) {
        return $(".report__workshop:nth-child(" + ++a + ")")
    }).forEach(function (b) {
        var a;
        b.each(function (b, c) {
            a && a.textContent == c.textContent ? ($(c).remove(), a.rowSpan++) : a = c
        })
    })
});


$(document).ready(function () {
    var urlParams = new URLSearchParams(window.location.search);
    if (urlParams.toString() == '') {
        set_period('прошлая неделя');
        $("#id_periods_selector").val('прошлая неделя');
        urlParams.append('periods_selector', 'прошлая+неделя');
        urlParams.append('start_date', $('#id_start_date').val());
        urlParams.append('end_date', $('#id_end_date').val());
        location.hash = urlParams.toString();
    }


    $("#id_empty_only").on('change', function () {
        if ($(this).is(':checked')) {
            $(this).attr('value', 'True');
        } else {
            $(this).attr('value', 'False');
        }
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

    $("#id_periods_selector").change(function (e) {
        var cur_val = $(this).val();
        set_period(cur_val);
    });

});

function formatDate(date) {
    var month = (date.getMonth() + 1).toString().padStart(2, '0');
    var day = date.getDate().toString().padStart(2, '0');
    return `${date.getFullYear()}-${month}-${day}`;
}

// function clearUrl() {
//     const urlParams = new URLSearchParams(window.location.search);
//     urlParams.delete('periods_selector');
//     urlParams.delete('start_date');
//     urlParams.delete('end_date');
//     location.hash = urlParams.toString();
// }

function set_period(period) {
    switch (period) {
        case 'прошлая неделя':
            var date = new Date();
            var dayOfWeek = date.getDay();
            var endPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() - dayOfWeek);
            var startPeriod = new Date(date.getFullYear(), date.getMonth(), date.getDate() - dayOfWeek - 6);
            $('#id_start_date').val(formatDate(startPeriod));
            $('#id_end_date').val(formatDate(endPeriod));
            $('#id_start_date').attr('readonly', true);
            $('#id_end_date').attr('readonly', true);
            break;
        case 'прошлый месяц':
            var date = new Date();
            var endPeriod = new Date(date.getFullYear(), date.getMonth(), 1);
            var startPeriod = new Date(date.getFullYear(), date.getMonth() - 1, 1);
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

