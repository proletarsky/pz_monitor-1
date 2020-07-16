//Открытие меню
$(document).ready(function (){
    var btn = $("#toggle-slidebar");
    btn.on("click", function (e) {
        e.preventDefault();
        var form = $("#wrapper"),nav = $("#sidebar-wrapper");
        form.toggleClass("toggled");
	nav.toggleClass("toggled");
    })

$.fn.loadWith = function(u){
    var c=$(this);
    $.get(u,function(d){
	d=$(d).find('#pagecontent').html();
        c.replaceWith(d);
//	graphicsData=$('#grada').text();
//	drawChart();


    });
};
//$("#test").loadWith($(this).parents('form').serialize());
	
/////$('#sendform').on('click', function (e) {
     ////   e.preventDefault();	
        //alert($(this).parents('form').serialize());
////	$("#pagecontent table").loadWith('?'+$(this).parents('form').serialize());
////    });

// убрать кнопку "вернуться" на главной
if(window.location.pathname=='/'){
$('a.goback').remove();
}

$(document).on('click', 'a.goback', function(e){
e.preventDefault();
if (document.referrer == "") {
    window.close()
} else {
//    history.back()
history.go(-1);
}
});

// Returns the ISO day of week
Date.prototype.getWeekDay = function() {
  var day = this.getDay();
  if(day==0) return 7;
  else return day;  
}

// Returns current week start date
Date.prototype.getWeekStartDate = function() {
  var date = new Date(this.getTime());      
  date.setDate(this.getDate()-(this.getWeekDay()-1));
  return date;     
}

// Returns current week end date
Date.prototype.getWeekEndDate = function() {
  var date = new Date(this.getTime());      
  date.setDate(this.getDate()+(7-this.getWeekDay()));
  return date;     
}

msInDay = 86400000;  // миллисекунд в сутках
currentDate = new Date;  // текущая дата
prevWeekDate = new Date(currentDate - (7 * msInDay)); // дата на прошлой неделе

prevWeekStartDate = prevWeekDate.getWeekStartDate();  // дата понедельника прошлой недели
prevWeekEndDate = prevWeekDate.getWeekEndDate();  // дата воскресенья прошлой недели




// Прилипание меню к верху страницы
 /* var navbar=$('.pz-header'),navtop = navbar.height() + navbar.offset().top,*.
  /* thead=$('thead'),
  theadtop = thead.offset().top,*/
/*  navheight=$('#sidebar-wrapper').height();
  $(window).scroll(function scrollfix() {
    $('#sidebar-wrapper').css(
      $(window).scrollTop() > navtop
        ? { 'position': 'fixed', 'top': '0' }
        : { 'position': 'absolute', 'top': 'auto' }
    );
*/
/*
   $('thead').css(
      $(window).scrollTop()+navheight > theadtop
        ? { 'position': 'fixed', 'top':navheight,'padding':'0 20px' }
        : { 'position': 'absolute', 'top': '-35px','padding':'0' }
    );
*/
/*
    return scrollfix;
  }());
*/
});
