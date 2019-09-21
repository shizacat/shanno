new Vue({
  el: "#project-page",
  delimiters: ['${', '}'],
  data: {
    total_docs: 20,
    current_page: 1,
    docs: [],
    docs_by_page: 10,  // Документов на странице
    docs_approved: 0,  // Документов проверено
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
      .catch(function(error) {
        console.log(error)
      });
    },
    getAllDocumentApproved: function(){
      self = this;

      axios.get("/api/project/" + this.project_id + "/documents_all_is_approved/")
      .then(function(response) {
        self.docs_approved = response.data.count;
      })
      .catch(function(error) {
        console.log(error)
      });
    },
    deleteDoc: function(doc_id) {
      self = this;

      axios.delete("/api/document/" + doc_id + "/")
        .then(function(response){
          self.getAllDocumentPage(self.current_page)
        })
        .catch(function(error) {
          console.log(error)
        });
    },
    gotoUrl: function(url) {
      window.location.href = url;
    }
  },
  filters: { 
    truncate: function(string, value) {
        return string.substring(0, value) + '...';
    }
  }
});