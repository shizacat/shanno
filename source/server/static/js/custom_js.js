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
	        identifier  : 'name',
	        rules: [
	          {
	            type   : 'empty',
	            prompt : 'Поле "Название проекта" не должно быть пустым'
	          }
	        ]
	      },
	      type: {
	      	identifier: 'type',
	      	rules: [
	      	{
	      		type: 'empty',
	      		prompt : 'Поле "Тип проекта" не должно быть пустым'
	      	}]
	      }
	    }
	  });

	var apiUrl = location.protocol + "//" + location.host + "/" + 'api/project/'

	$('.ui.form .submit.button')
		.api({
    	url: apiUrl,
    	method : 'POST',
    	serializeForm: true,
    	beforeSend: function(settings) {

    	},
    	onSuccess: function(data) {

    	}
  	});
});
