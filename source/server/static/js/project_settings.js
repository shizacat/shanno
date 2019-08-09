new Vue({
  el: "#project-settings",
  methods: {
    deleteProject: function(project_id) {
      axios.delete("/api/project/" + project_id + "/")
        .then(function (response) {
            location.href = '/projects/';
        })
        .catch(function (error) {
          console.log("Получена ошибка");
          console.log(error);
        });
    }
  }
});