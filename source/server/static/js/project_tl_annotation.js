new Vue({
  el: "#project-annotaion",
  delimiters: ['${', '}'],
  data: {
    docs: [],  // Список объектов документ в проекте
    docs_cindex: 0, // Индекс текущего документа
    doc_data: [],
    bt_prev_enable: false,
    bt_next_enable: false
  },
  computed: {
    doc_id: function(){
      return window.location.href.split("?doc=")[1];
    },
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
    created() {
      this.getDocsListbyProject()
      this.getDocSequence(this.doc_id);
  },
  methods: {
    onNext: function () {
      this.docs_cindex++;
      this.getDocSequence(this.docs[this.docs_cindex].id);
      this.setupButton();
      this.setupUrlDocByIndex(this.docs_cindex);
    },
    onPrev: function() {
      this.docs_cindex--;
      this.getDocSequence(this.docs[this.docs_cindex].id);
      this.setupButton();
      this.setupUrlDocByIndex(this.docs_cindex);
    },
    getDocSequence: function(doc_id) {
      self = this;
      axios.get("/api/document/" + doc_id + "/")
      .then(function(response){
        self.doc_data = response.data.sequences
        // console.log(response)
      })
      .catch(function(error) {
        console.log(error)
      });
    },
    getDocsListbyProject: function(){
      self = this;
      axios.get("/api/project/" + this.project_id + "/documents_list_simple/")
      .then(function(response){
        self.docs = response.data

        // Текущая позиция в массиве документов
        for (var i=0 in self.docs){
          if (self.docs[i].id == self.doc_id){
            self.docs_cindex = parseInt(i);
            break;
          }
        }
        // Setup Button
        self.setupButton()
      })
      .catch(function(error) {
        console.log(error)
      });
    },
    setupButton: function(){
      this.bt_prev_enable = (this.docs_cindex != 0);
      this.bt_next_enable = (this.docs_cindex != (this.docs.length - 1));
    },
    setupUrlDocByIndex: function(doc_index){
      var newurl = "".concat(
        window.location.protocol, "//",
        window.location.host, 
        window.location.pathname,
        "?doc=", this.docs[doc_index].id
      );
      window.history.pushState(null, null, newurl);
    }
  }
});