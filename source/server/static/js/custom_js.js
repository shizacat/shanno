$(document).ready(function() {
    // dropdown initialization
    $('.ui.dropdown').dropdown();

    // project form validation rules
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
    //           identifier: 'type',
    //           rules: [
    //           {
    //               type: 'empty',
    //               prompt : 'Поле "Тип проекта" не должно быть пустым'
    //           }]
    //       }
    //     }
    //   });

    // var apiUrl = '/api/project/';

    // $('.ui.form .submit.button')
    //     .api({
    //     url: apiUrl,
    //     method : 'POST',
    //     serializeForm: true,
    //     beforeSend: function(settings) {

    //     },
    //     onSuccess: function(data) {

    //     }
    //   });

    // new Vue({
    //   el: "#app-form",
    //   data() {
    //     return {
    //       current: null,
    //       options: [{
    //         text: 'Male',
    //         value: 1,
    //       }, {
    //         text: 'Female',
    //         value: 2,
    //       }],
    //     };
    //   },
    // });

    // Обработчик формы
    new Vue({
        el: "#app-form",
        data: {
          name: "",
          description: "",
          type: "",
        },
        methods: {
            onSubmit: function(){
                axios.post("/api/project/?format=json",
                  JSON.stringify({
                      name: this.name,
                      description: this.description,
                      type: this.type
                  })
                )
                .then(function (response) {
                  console.log(response);
                })
                .catch(function (error) {
                  console.log("Получена ошибка");
                  console.log(error);
                });
            }
        }
    });
});
