new Vue({
  el: "#project-page",
  delimiters: ['${', '}'],
  data: {
    total_docs: 20,
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
  created() {
    this.getAllDocumentPage(1);
    this.getAllDocumentApproved();
  },
  methods: {
    getAllDocumentPage: function(page){
      self = this;

      axios.get("/api/project/" + this.project_id + "/documents_list/?page=" + page)
      .then(function(response) {
        self.total_docs = response.data.count;
        self.docs = response.data.results;
        self.current_page = page;
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