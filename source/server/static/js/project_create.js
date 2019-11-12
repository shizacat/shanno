new Vue({
    el: "#app-projects",
    delimiters: ['${', '}'],
    data: {
      name: "",
      description: null,
      type: "",
      st_show: false,
      st_value: "",
    },
    methods: {
      onSubmit: function(){
        self = this;
        axios.post("/api/project/",
            JSON.stringify({
                name: this.name,
                description: this.description,
                type: this.type
            }),
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )
          .then(function (response) {
            self.name = "";
            self.description = "";
            self.type = "";
          })
          .catch(this.addErrorApi);
      },
      addError: function(msg){
        this.st_value = msg;
        this.st_show = true;
      },
      addErrorApi: function(error) {
        let msg = "";
        if (typeof error.response !== 'undefined'){
          msg = "Ошибка: [" + error.response.status + "] ";
          msg += JSON.stringify(error.response.data);
        } else {
          msg = "Ошибка: " + error.toString();
        }
        this.addError(msg);
      }
    }
  });
