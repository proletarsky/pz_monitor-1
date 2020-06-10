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
	$('#sendform').on('click', function (e) {
        e.preventDefault();	
        //alert($(this).parents('form').serialize());
	$("#pagecontent table").loadWith('?'+$(this).parents('form').serialize());
	
        
	
    });



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
