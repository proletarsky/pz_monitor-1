$(document).ready(function () {
    var btn = $("#toggle-slidebar");
    btn.on("click", function (e) {
        e.preventDefault();
        var form = $("#wrapper");
        form.toggleClass("toggled");
        console.log("Hi, bitch!");
        console.log(form);
    })
});
