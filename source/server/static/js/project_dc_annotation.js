var router = new VueRouter({
    mode: 'history',
    routes: []
});

new Vue({
  router,
  el: "#project-dc-annotaion",
  delimiters: ['${', '}'],
  data: {
    docs: [],             // Список объектов документ в проекте
    docs_cindex: 0,       // Индекс текущего документа
    doc_data: [],         // Массив seq документа
    doc: {},              // Сам документ
    labels: [],           // Массив меток
    active_labels: [],
    bt_prev_enable: false,
    bt_next_enable: false,
    is_approved: false,    // Зуб даю верный
    filter: {},
    is_open_delete: false,
    st_show: false,
    st_variant: "is-danger",
    st_value: "",
  },
  computed: {
    doc_id: function(){
      return this.$route.query.doc;
    },
    project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  created() {
    self = this;

    if ("approved" in this.$route.query){
      this.filter.approved = parseInt(this.$route.query.approved);
    }

    this.getDocsListbyProject()

    // GetLabels
    axios.get("/api/project/" + this.project_id + "/tl_labels_list/")
    .then(function(response){
      self.labels = response.data;
      self.getDocSequence(self.doc_id);
    })
    .catch(this.addErrorApi);

    this.getActiveLabels()

    // Keys
    document.addEventListener('keyup', this.onKey);
  },
  methods: {
    onKey: function(e){
      switch(e.keyCode) {
        case 37:
          // Left
          if (this.bt_prev_enable)
            this.onPrev();
          break;
        case 39:
          // Right
          if (this.bt_next_enable)
            this.onNext();
          break;
        default:
          let prefix_key = this.toStringPreffixKey(e);
          let key = String.fromCharCode(e.keyCode).toLowerCase();
          // ---
          for (i in this.labels){
            let label = this.labels[i];
            if (label.prefix_key == prefix_key)
              if (label.suffix_key == key) {
                this.createLabel(label.id);
              }
          }
      }
    },
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
    onDeleteLabel: function(label_id){
      axios.post(
        "/api/document/" + this.doc.id + "/label_set/",
        JSON.stringify({
            "label_id": label_id,
            "value": 0
        }),
        {
          headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      )
      .then(function(response){
        self.getActiveLabels()
      })
      .catch(this.addErrorApi);
    },
    openDelete: function() {
      this.is_open_delete = true;
    },
    closeDelete: function() {
      this.is_open_delete = false;
    },
    deleteDoc: function() {
      self = this;

      axios.delete(
        "/api/document/" + self.doc.id + "/",
        {
          headers: {
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(response){
        self.is_open_delete = false
        if (self.bt_next_enable == true) {
          self.onNext();
          self.getDocsListbyProject();
        } else if (self.bt_prev_enable == true) {
          self.onPrev();
          self.getDocsListbyProject();
        } else {
          location.href = '/projects/' + self.project_id;
        }
      })
      .catch(this.addErrorApi);
    },
    onChangeApproved: function(){
      if (this.is_approved){
        axios.post(
          "/api/document/" + this.doc.id + "/approved/",
          "",
          {
            headers: {
              "X-CSRFToken": this.$cookies.get("csrftoken")
            }
          }
        )
        .then(function(response){
        })
        .catch(this.addErrorApi);
      }else{
        axios.post(
          "/api/document/" + this.doc.id + "/unapproved/",
          "",
          {
            headers: {
              "X-CSRFToken": this.$cookies.get("csrftoken")
            }
          }
        )
        .then(function(response){
        })
        .catch(this.addErrorApi);
      }
    },
    resetLabels: function(){
      self = this;
      axios.post(
        "/api/document/" + this.doc.id + "/reset/",
        "",
        {
          headers: {
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      )
      .then(function(response){
        self.getDocSequence(self.doc.id)
      })
      .catch(this.addErrorApi);
    },
    getDocSequence: function(doc_id) {
      self = this;
      axios.get("/api/document/" + doc_id + "/")
      .then(function(response){
        self.doc_data = response.data.sequences;
        self.doc = response.data;
        self.is_approved = self.doc.approved;
      })
      .catch(this.addErrorApi);
    },
    getDocsListbyProject: function(){
      self = this;
      axios.get(
        "/api/project/" + this.project_id + "/documents_list_simple/",
        {params: this.filter}
      )
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
      .catch(this.addErrorApi);
    },
    setupButton: function(){
      this.bt_prev_enable = (this.docs_cindex != 0);
      this.bt_next_enable = (this.docs_cindex != (this.docs.length - 1));
    },
    getActiveLabels: function(){
      self = this;
      axios.get("/api/document/" + this.doc_id + "/labels/")
      .then(function(response){
        console.log(response.data)
        let label_ids = response.data.filter(x => {
          if (x.value === 1) {
            return false;
          }
          return true;
        }).map(x => x.id);
        console.log(label_ids);
        self.active_labels = self.labels.filter(item => {
          return label_ids.indexOf(item.id) == -1;
        });
        console.log(self.active_labels);
      })
      .catch(this.addErrorApi);
    },
    createLabel: function(label_id){
      var self = this;

      axios.post(
        "/api/document/" + this.doc.id + "/label_set/",
        JSON.stringify({
            "label_id": label_id,
            "value": 1
        }),
        {
          headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      )
      .then(function(response){
        self.getActiveLabels()
      })
      .catch(this.addErrorApi);
    },
    setupUrlDocByIndex: function(doc_index){
      q = Object.assign({}, self.$route.query);
      q.doc = this.docs[doc_index].id;
      self.$router.push({query: q});
    },
    toStringPreffixKey: function(e){
      if (e.ctrlKey & !e.shiftKey)
        return "ctrl";
      else if (!e.ctrlKey & e.shiftKey)
        return "shift";
      else if (e.ctrlKey & e.shiftKey)
        return "ctrl+shift";
      return "";
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
  },
});
