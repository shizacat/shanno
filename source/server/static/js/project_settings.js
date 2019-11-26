new Vue({
  el: "#project-settings",
  delimiters: ['${', '}'],
  data: {
    members: Array,
    new_member: null,
    is_open_delete: null,
    is_open_project_delete: false,
    active_edit: null,
    st_show: false,
    st_variant: "is-danger",
    st_value: "",
  },
  computed: {
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  created() {
    this.getMembers();
  },
  methods: {
    deleteProject: function(project_id) {
      axios.delete(
        "/api/project/" + this.project_id + "/",
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
    addMember() {
      this.new_member = {
        role: "view",
        username: ""
      };
    },
    cancelCreate() {
      this.new_member = null;
    },
    postMember() {
      self = this;
      axios.post(
        "/api/project/" + this.project_id + "/permission/",
        this.new_member,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(response){
        self.cancelCreate();
        self.getMembers();
      })
      .catch(this.addErrorApi);
    },
    getMembers() {
      self = this;
      axios.get("/api/project/" + this.project_id + "/permission/")
        .then(function(response){
          self.members = response.data;
          self.members.reverse();
        })
        .catch(this.addErrorApi)
    },
    closeDelete: function() {
      this.is_open_delete = null
    },
    openDelete: function(index) {
      this.is_open_delete = index
    },
    editLabel(member) {
      this.clone_member = Object.assign({}, member);
      this.active_edit = member;
    },
    saveEditChanges(member) {
      self = this;
      this.active_edit = null;
      axios.put(
        "/api/project/" + this.project_id + "/permission/",
        member,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(){
        self.members;
      })
      .catch(this.addErrorApi);
    },
    repealEdit(member) {
      this.active_edit = null;
      Object.assign(member, this.clone_member);
    },
    deleteMember(member) {
      self = this;
      axios.delete(
        "/api/project/" + this.project_id + "/permission/",
        {
          data: { username: member.username },
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(){
        let index = self.members.indexOf(member);
        self.is_open_delete = null
        self.members.splice(index, 1);
      })
      .catch(this.addErrorApi);
    },
    openProjectDelete: function() {
      this.is_open_project_delete = true
    },
    closeProjectDelete: function() {
      this.is_open_project_delete = false
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