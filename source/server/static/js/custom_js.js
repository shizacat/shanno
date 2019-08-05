$(document).ready(function() {
	// dropdown initialization
	// $('.ui.dropdown')
 //  .dropdown();

 //  // project form validation rules
	// $('.ui.form')
	//   .form({
	//     on: 'blur',
	//     fields: {
	//       name: {
	//         identifier  : 'name',
	//         rules: [
	//           {
	//             type   : 'empty',
	//             prompt : 'Поле "Название проекта" не должно быть пустым'
	//           }
	//         ]
	//       },
	//       type: {
	//       	identifier: 'type',
	//       	rules: [
	//       	{
	//       		type: 'empty',
	//       		prompt : 'Поле "Тип проекта" не должно быть пустым'
	//       	}]
	//       }
	//     }
	//   });

	// var apiUrl = location.protocol + "//" + location.host + "/" + 'api/project/'

	// $.getJSON(apiUrl, function(data){
 //  	var project_data = '';
 //  	var project_json = data.reverse()
 //  	$.each(project_json, function(key, value) {
 //  		project_data += '<div class="item">';
 //  		project_data += '<div class="right floated content">';
 //  		project_data += '<button class="mini circular ui icon submit button">';
 //  		project_data += '<i class="red icon close"></i>'
 //  		project_data += '</button></div>'
 //  		project_data += '<i class="large chevron circle right middle aligned icon"></i>';
 //  		project_data += '<div class="content">';
 //  		project_data += '<div class="header">'+value.name+'</div>';
 //  		project_data += '<div class="description">'+value.description+'</div></div></div>'
 //  	});
 //  	$('.ui.relaxed.divided.project.list').append(project_data);
	// });

	// $('.ui.form .submit.button')
	// 	.api({
 //    	url: apiUrl,
 //    	method : 'POST',
 //    	serializeForm: true
 //  	});
});

Vue.component('list-component', {
	template: `
	<div class="item">
		<div class="right floated content">
			<button class="mini circular ui icon submit button">
				<i class="red icon close"></i>
			</button>
		</div>
		<i class="large chevron circle right middle aligned icon"></i>
		<div class="content">
			<div class="header">{{ project.name }}</div>
			<div class="description">{{ project.description }}</div>
		</div>
	</div>
		`,
	props: {
    project: Object
  }
});

var prj_list = new Vue({
	el: '#prj_list',
  // data: {
  //   projects: [{"id":6,"type":"text_label","name":"test","description":""},{"id":7,"type":"text_label","name":"test3","description":""},{"id":8,"type":"text_label","name":"test2","description":"asdasdd"},{"id":9,"type":"text_label","name":"test4","description":"fsfdsfdsf"},{"id":10,"type":"text_label","name":"test5","description":""},{"id":11,"type":"text_label","name":"test7","description":""},{"id":12,"type":"text_label","name":"test8","description":""},{"id":13,"type":"text_label","name":"test10","description":""},{"id":14,"type":"text_label","name":"test12","description":""},{"id":15,"type":"text_label","name":"test14","description":""},{"id":16,"type":"text_label","name":"test14","description":""},{"id":17,"type":"text_label","name":"sdfsdf","description":""},{"id":18,"type":"text_label","name":"dsgdfgdfg","description":"fgsdfgsdfg dfg dfg afg dfgadfga glikfjlksdfjoi"},{"id":19,"type":"text_label","name":"dfk fkseio","description":"sfj jjpfsof f sdfo spdf e"},{"id":20,"type":"text_label","name":"asdasd","description":"fsdfef"},{"id":21,"type":"text_label","name":"13123123","description":"fdgdfgdfgdfg"},{"id":22,"type":"text_label","name":"govno","description":"jopppa"},{"id":23,"type":"text_label","name":"asdasdasd","description":"asdasdasd"},{"id":24,"type":"text_label","name":"asdasdasd","description":"asdasdasd"},{"id":25,"type":"text_label","name":"asdasdasd1","description":"asdasdasd"},{"id":26,"type":"text_label","name":"asdasdsad","description":"ffgfdf"},{"id":27,"type":"text_label","name":"asdasd","description":"ffgfff"},{"id":28,"type":"text_label","name":"dadasdasdasd","description":"asdasdasdasd"},{"id":29,"type":"text_label","name":"werwer","description":"werwerwer"},{"id":30,"type":"text_label","name":"werwer","description":"werwerwer"}]
  // }
  data () {
    return {
    	projects: null
    }
  },
  mounted () {
    axios
      .get('/api/project/?format=json')
      .then(response => (this.projects = response.data))
  		.catch(error => console.log(error))
  }
});



var prj_form = new Vue({
  el: '#prj_form',
  data: function(){
  	return {
  	name: "",
    description: "",
    type: ""
  	}
  },
  methods: {
    createUser() {
      axios.post('/api/project/?format=json', {
        name: this.name,
        description: this.description,
        type: this.type
      })
      .then(function (response) {
          console.log(response);
      })
      .catch(function (error) {
          console.log(error);
      });
    }
  }
});

