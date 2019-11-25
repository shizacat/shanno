new Vue({
  el: "#project-settings",
  delimiters: ['${', '}'],
  data: {
    new_permission: null,
    st_show: false,
    st_variant: "is-danger",
    st_value: "",
  },
  computed: {
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  methods: {
    deleteProject: function(project_id) {
      axios.delete(
        "/api/project/" + project_id + "/",
        {
          headers: {
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function (response) {
          location.href = '/';
      })
      .catch(this.addErrorApi);
    },
    createPermission() {
      this.new_permission = {
        is_view: true,
        is_change: false,
        project: parseInt(this.project_id),
        user: ""
      };
    },
    cancelCreate() {
      this.new_permission = null;
    },
    postPermission() {
      self = this;
      axios.post(
        "/api/project/" + this.project_id + "/permission/",
        this.new_permission,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(response){
        self.cancelCreate();
      })
      .catch(this.addErrorApi);
    },
    addError: function(msg){
      this.st_variant = "is-danger";
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