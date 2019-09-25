new Vue({
  el: "#project-settings",
  delimiters: ['${', '}'],
  data: {
    st_show: false,
    st_variant: "danger",
    st_value: "",
  },
  methods: {
    deleteProject: function(project_id) {
      axios.delete("/api/project/" + project_id + "/")
        .then(function (response) {
            location.href = '/projects/';
        })
        .catch(this.addErrorApi);
    },
    addError: function(msg){
      this.st_variant = "danger";
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