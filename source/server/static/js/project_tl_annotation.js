var router = new VueRouter({
    mode: 'history',
    routes: []
});

new Vue({
  router,
  el: "#project-annotaion",
  delimiters: ['${', '}'],
  data: {
    docs: [],             // Список объектов документ в проекте
    docs_cindex: 0,       // Индекс текущего документа
    doc_data: [],         // Массив seq документа
    doc: {},              // Сам документ
    data_render: [],      // Массив обработанных seq
    doc_render: {},
    labels: [],           // Массив меток
    labels_hash: {},      // Словарь по индексу доступа к объекту меток
    sel_offset_start: -1, // Начало/конец выделенного участка
    sel_offset_end: -1,
    sel_seq_id: -1,
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
      for (var i = 0; i < response.data.length; i++){
        self.labels_hash[response.data[i].id] = response.data[i]
      }
      self.labels = response.data;
      self.getDocSequence(self.doc_id);
    })
    .catch(this.addErrorApi);

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
    onDeleteLabel: function(label_seq_id, seq_id, i_chunk){
      var labels = this.doc_render[seq_id].obj.labels;
      for(var j = 0; j < labels.length; j++){
        if (labels[j].id == label_seq_id){
          this.doc_render[seq_id].obj.labels.splice(j, 1);
          break;
        }
      }
      
      this.doc_render[seq_id].chunks = this.renderCreateChunks(
        this.doc_render[seq_id].obj
      );

      axios.delete(
        "/api/tl_seq_label/" + label_seq_id + "/",
        {
          headers: {
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      )
      .then(function(response){
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
        self.render();
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
    render: function(){
      this.doc_render = {};
      for(var i = 0; i < this.doc_data.length; i++){
        // Sequence from document
        Vue.set(
          this.doc_render,
          this.doc_data[i].id,
          {
            obj: this.doc_data[i],
            chunks: this.renderCreateChunks(this.doc_data[i])
          }
        );
      };
    },
    renderCreateChunks: function(sequence){
      // Создает массив с кусками из Sequence
      // sequence - это одноименный объект
      var chunks = new Array;
      var labels = sequence.labels;
      var lastOffset = 0;
      var tStr = sequence.text;

      for (var j = 0; j < labels.length; j++){
        var offset = labels[j].offset_start;
        var end = labels[j].offset_stop;

        if (offset != 0){
          chunks.push({
            type: "text",
            text: tStr.substring(lastOffset, offset)
          });
        };

        chunks.push({
          type: "label",
          text: tStr.substring(offset, end),
          obj: labels[j]
        });
        lastOffset = end;
      };
      if (lastOffset != tStr.length){
        chunks.push({
          type: "text",
          text: tStr.substring(lastOffset, tStr.length)
        });
      }

      return chunks
    },
    createLabel: function(label_id){
      if ((this.sel_offset_start < 0) || (this.sel_offset_end < 0))
        return;

      var self = this;

      axios.post(
        "/api/tl_seq_label/",
        JSON.stringify({
            offset_start: this.sel_offset_start,
            offset_stop: this.sel_offset_end,
            sequence: this.sel_seq_id,
            label: label_id
        }),
        {
          headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      )
      .then(function(response){
        var labels = self.doc_render[self.sel_seq_id].obj.labels;
        labels = labels.concat(response.data);
        labels.sort(function(a, b){
          var s1 = a.offset_start;
          var s2 = b.offset_start;
          if (s1 < s2) return -1;
          if (s1 > s2) return 1;
          return 0;
        });
        self.doc_render[self.sel_seq_id].obj.labels = labels;

        self.doc_render[self.sel_seq_id].chunks = self.renderCreateChunks(
          self.doc_render[self.sel_seq_id].obj
        );
        self.selResetRange();
      })
      .catch(this.addErrorApi);
    },
    selResetRange: function(){
      // Reset selection
      this.sel_offset_start = -1;
      this.sel_offset_end = -1;
      this.sel_seq_id = -1;
    },
    setSelectedRange: function(seq_id){    
      var offsetChunk = 0;
      var offsetChunkEnd = 0;
      var offsetStartDoc = 0;
      var offsetEndDoc = 0;

      // Senstive onDelete
      if (window.getSelection().rangeCount == 0)
        return;

      var range = window.getSelection().getRangeAt(0);
      var chunk_id = range.startContainer.parentElement.id;

      if (range.collapsed){
        this.selResetRange()
        return;
      }

      if (this.doc_render[seq_id].chunks[chunk_id].hasOwnProperty("obj")){
        this.selResetRange();
        return;
      }

      if (range.startContainer != range.endContainer){
        this.selResetRange();
        return;
      }
        
      if (chunk_id > 0){
        offsetChunk = this.doc_render[seq_id].chunks[chunk_id-1].obj.offset_stop;
      }
      offsetChunkEnd = offsetChunk + this.doc_render[seq_id].chunks[chunk_id].text.length;
      offsetEndDoc = offsetChunk + range.endOffset;
      offsetStartDoc = offsetChunk + range.startOffset;

      // Выравниваем по слово Начало
      var text = this.doc_render[seq_id].obj.text
      if (offsetStartDoc > 0){
        if (text.substring(offsetStartDoc, offsetStartDoc + 1) == " "){
          for (var i = offsetStartDoc + 1; i < offsetEndDoc; i++){
            if (text.substring(i, i + 1) != " ")
              break;
          }
          offsetStartDoc = i;
        }else if (text.substring(offsetStartDoc - 1, offsetStartDoc) != " "){
          for (var i = offsetStartDoc; i > offsetChunk; i--){
            if (text.substring(i - 1, i) == " ")
              break;
          }
          offsetStartDoc = i;
        }
      }
      // Выравниваем по слово Конец
      if (offsetEndDoc != offsetChunkEnd){
        if (text.substring(offsetEndDoc - 1, offsetEndDoc) == " "){
          for (var i = offsetEndDoc - 1; i > offsetStartDoc; i--){
            if (text.substring(i, i - 1) != " ")
              break;
          }
          offsetEndDoc = i;
        }else if (text.substring(offsetEndDoc, offsetEndDoc + 1) != " "){
          for (var i = offsetEndDoc; i < offsetChunkEnd; i++){
            if (text.substring(i, i + 1) == " ")
              break;
          }
          offsetEndDoc = i;
        }
      }

      this.sel_offset_start = offsetStartDoc;
      this.sel_offset_end = offsetEndDoc;
      this.sel_seq_id = seq_id;
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
