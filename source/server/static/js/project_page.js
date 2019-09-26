var router = new VueRouter({
    mode: 'history',
    routes: []
});

new Vue({
  router,
  el: "#project-page",
  delimiters: ['${', '}'],
  data: {
    docs_total: 0,
    current_page: 1,
    docs: [],
    docs_by_page: 10,  // Документов на странице
    docs_approved: 0,  // Документов проверено
    st_show: false,
    st_variant: "danger",
    st_value: "",
  },
  computed: {
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  async created() {
    let page = 1;
    if ("page" in this.$route.query){
      page = parseInt(this.$route.query.page);
    };

    this.getAllDocumentApproved();
    await this.getCountDocuments();
    this.current_page = page;
  },
  methods: {
    getCountDocuments: function(){
      self = this;

      return axios.get("/api/project/" + this.project_id + "/documents_list/?page=1")
        .then(function(response) {
          self.docs_total = response.data.count;
          self.docs = response.data.results;
        })
        .catch(this.addErrorApi);
    },
    getAllDocumentPage: function(page){
      self = this;

      axios.get("/api/project/" + this.project_id + "/documents_list/?page=" + page)
      .then(function(response) {
        self.docs = response.data.results;
        // Set Page
        if (page != self.$route.query.page){
          q = Object.assign({}, self.$route.query);
          q.page = page;
          self.$router.push({query: q});
        }
      })
      .catch(this.addErrorApi);
    },
    getAllDocumentApproved: function(){
      self = this;

      axios.get("/api/project/" + this.project_id + "/documents_all_is_approved/")
      .then(function(response) {
        self.docs_approved = response.data.count;
      })
      .catch(this.addErrorApi);
    },
    deleteDoc: function(doc_id) {
      self = this;

      axios.delete("/api/document/" + doc_id + "/")
      .then(function(response){
        self.getAllDocumentPage(self.current_page)
      })
      .catch(this.addErrorApi);
    },
    gotoUrl: function(url) {
      window.location.href = url;
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
  },
  filters: { 
    truncate: function(string, value) {
        return string.substring(0, value) + '...';
    }
  }
});