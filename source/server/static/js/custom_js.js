$(document).ready(function() {
  $(".masthead").visibility({
    once: false,
    onBottomPassed: function() {
      $(".fixed.menu").transition("fade in");
    },
    onBottomPassedReverse: function() {
      $(".fixed.menu").transition("fade out");
    }
  });
  $(".ui.sidebar").sidebar("attach events", ".toc.item");
  $('.ui .item').on('click', function() {
        $('.ui .item').removeClass('active');
        $(this).addClass('active');
    });
});
