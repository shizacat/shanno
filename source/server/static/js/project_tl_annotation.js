String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

new Vue({
  el: "#project-annotaion",
  delimiters: ['${', '}'],
  data: {
    docs: [],         // Список объектов документ в проекте
    docs_cindex: 0,   // Индекс текущего документа
    doc_data: [],     // Массив seq документа
    data_render: [],  // Массив обработанных seq
    doc_render: {},
    labels: [],       // Массив меток
    labels_hash: {},  // Словарь по индексу доступа к объекту меток
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
    self = this;
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
    .catch(function(error){
      console.log(error);
    })
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
      

      axios.delete("/api/tl_seq_label/" + label_seq_id + "/")
      .then(function(response){
        console.log("Complite");
      })
      .catch(function(error) {
        console.log(error);
      });
    },
    getDocSequence: function(doc_id) {
      self = this;
      axios.get("/api/document/" + doc_id + "/")
      .then(function(response){
        self.doc_data = response.data.sequences;
        // self.renderData();
        self.render();
      })
      .catch(function(error) {
        console.log(error);
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
    render: function(){
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
      console.log("doc_data", this.doc_data);
      console.log("doc_render", this.doc_render);
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
    textPart: function(text, label){

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
  },
  components: {
    'tl-label': {
      data: function () {
        return {
          clr_b: 0,
          clr_t: "black",
          text: "hh"
        }
      },
      template: '<p class="tl_anno_row"></p>'
      // "<span class='tag is-normal' :style=\"{'background-color': clr_b, color: clr_t}\">{{text}} - oo</span>"
    }
  }
});