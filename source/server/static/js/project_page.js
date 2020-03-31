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
    stat_docs_approved: 0,  // Документов проверено
    stat_docs_total: 0,     // Всего документов в наборе данных
    filter_approved: null,
    filter: {},
    st_show: false,
    st_variant: "danger",
    st_value: "",
    is_open_delete: null,
  },
  computed: {
    project_id: function(){
      return window.location.href.split("/")[4];
    },
    page_id: function(){
      if ("page" in this.$route.query){
        return parseInt(this.$route.query.page);
      } else {
        return 1
      }
    },
    last_page: function(){
      return Math.ceil(this.docs_total / this.docs_by_page)
    }
  },
  async created() {
    let page = 1;
    if ("page" in this.$route.query){
      page = parseInt(this.$route.query.page);
    };
    if ("approved" in this.$route.query){
      this.filter.approved = parseInt(this.$route.query.approved);
      this.filter_approved = this.filter.approved;
    }

    this.getAllDocumentApproved();
    await this.getCountDocuments();
    this.current_page = page;
  },
  methods: {
    getCountDocuments: function(){
      self = this;

      let p = Object.assign({}, this.filter, {page: this.page_id});
      return axios.get(
        "/api/project/" + this.project_id + "/documents_list/",
        {params: p})
      .then(function(response) {
        self.docs_total = response.data.count;
        self.docs = response.data.results;
      })
      .catch(this.addErrorApi);
    },
    getAllDocumentPage: function(page){
      self = this;

      let p = Object.assign({}, this.filter, {page: page});
      axios.get(
        "/api/project/" + this.project_id + "/documents_list/",
        {params: p}
        )
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
        self.stat_docs_approved = response.data.count;
        self.stat_docs_total = response.data.total;
      })
      .catch(this.addErrorApi);
    },
    deleteDoc: function(doc_id, index) {
      self = this;

      axios.delete(
        "/api/document/" + doc_id + "/",
        {
          headers: {
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(response){
        self.is_open_delete = null
        self.docs_total -= 1
        self.docs.splice(index,1)
      })
      .catch(this.addErrorApi);
    },
    gotoAnnotation: function(doc_id){
      let q = Object.assign({}, this.filter);
      q.doc = doc_id;
      window.location.href = "annotation?" + new URLSearchParams(q).toString();
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
    },
    changeFilterApproved: async function(){
      q = Object.assign({}, self.$route.query);

      if (this.filter_approved == null){
        if (this.filter.hasOwnProperty("approved")){
          delete this.filter["approved"];
          delete q["approved"];
        }
      }else{
        this.filter.approved = this.filter_approved;
        q.approved = this.filter_approved;
      };
      
      // Update URL
      self.$router.push({query: q});

      // Update docs list
      this.getAllDocumentApproved();
      await this.getCountDocuments();
      this.current_page = 1;
    },
    openDelete: function(index) {
      this.is_open_delete = index;
    },
    closeDelete: function() {
      this.is_open_delete = null
    },
  },
  filters: { 
    truncate: function(string, value) {
        return string.substring(0, value) + '...';
    }
  }
});