window.addEventListener("load", function(event) {

  new Vue({
    el: "#app-projects",
    data: {
      projects: [],
      name: "",
      description: null,
      type: "",
    },
    created() {
      this.getAllProjects();
    },
    methods: {
      getAllProjects: function() {
        self = this;

        axios.get("/api/project/")
          .then(function (response) {
            self.projects = response.data;
          })
          .catch(function (error) {
            console.log("Получена ошибка");
            console.log(error);
          });
      },
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
            self.projects.push(response.data);
            self.name = "";
            self.description = "";
            self.type = "";
          })
          .catch(function (error) {
            console.log("Получена ошибка");
            console.log(error);
          });
      }
    }
  });

});
