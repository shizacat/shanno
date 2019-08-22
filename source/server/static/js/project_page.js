new Vue({
  el: "#project-page",
  delimiters: ['${', '}'],
  data: {
    total_docs: 20,
    processed_docs: 8,
    current_page: 1,
    docs: [],
    docs_by_page: 10,  // Документов на странице
  },
  computed: {
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  created() {
    this.getAllDocumentPage(1);
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
    deleteDoc: function(doc_id) {
      axios.delete("/api/document/" + doc_id + "/")
        .then(function(response){
          this.getAllDocumentPage(this.current_page)
        })
        .catch(function(error) {
          console.log(error)
        });
    }
  },
  filters: { 
    truncate: function(string, value) {
        return string.substring(0, value) + '...';
    }
  }
});