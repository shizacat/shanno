$(document).ready(function() {
  $(".ui.sidebar").sidebar("attach events", ".toc.item");
  $('.ui .item').on('click', function() {
        $('.ui .item').removeClass('active');
        $(this).addClass('active');
    });
});
