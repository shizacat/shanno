$(document).ready(function() {
$('.ui.form')
  .form({
    on: 'blur',
    fields: {
      empty: {
        identifier  : 'project-name',
        rules: [
          {
            type   : 'empty',
            prompt : 'Please enter a name'
          }
        ]
      },
      dropdown: {
        identifier  : 'project-description',
        rules: [
          {
            type   : 'empty',
            prompt : 'Please enter a description'
          }
        ]
      },
      checkbox: {
        identifier  : 'file-input',
        rules: [
          {
            type   : 'empty',
            prompt : 'Please upload a file'
          }
        ]
      }
    }
  });
});
