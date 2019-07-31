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

	$.getJSON(apiUrl, function(data){
  	var project_data = '';
  	var project_json = data.reverse()
  	$.each(project_json, function(key, value) {
  		project_data += '<div class="item">';
  		project_data += '<div class="right floated content">';
  		project_data += '<button class="mini circular ui icon submit button">';
  		project_data += '<i class="red icon close"></i>'
  		project_data += '</button></div>'
  		project_data += '<i class="large chevron circle right middle aligned icon"></i>';
  		project_data += '<div class="content">';
  		project_data += '<div class="header">'+value.name+'</div>';
  		project_data += '<div class="description">'+value.description+'</div></div></div>'
  	});
  	$('.ui.relaxed.divided.project.list').append(project_data);
	});

	$('.ui.form .submit.button')
		.api({
    	url: apiUrl,
    	method : 'POST',
    	serializeForm: true
  	});
});
