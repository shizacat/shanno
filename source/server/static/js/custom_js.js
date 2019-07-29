$(document).ready(function() {
	// dropdown initialization
	$('.ui.dropdown')
  .dropdown();

  // project form validation rules
	$('.ui.form')
	  .form({
	    on: 'blur',
	    fields: {
	      name: {
	        identifier  : 'project-name',
	        rules: [
	          {
	            type   : 'empty',
	            prompt : 'Поле "Название проекта" не должно быть пустым'
	          }
	        ]
	      },
	      type: {
	      	identifier: 'project-type',
	      	rules: [
	      	{
	      		type: 'empty',
	      		prompt : 'Поле "Тип проекта" не должно быть пустым'
	      	}]
	      }
	    }
	  });
});
