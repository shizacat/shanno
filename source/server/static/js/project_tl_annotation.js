new Vue({
  el: "#project-annotaion",
  delimiters: ['${', '}'],
  data: {
    docs: [],  // Список объектов документ в проекте
    docs_cindex: 0, // Индекс текущего документа
    doc_data: [],
    data_render: [],  // Массив обработанных seq
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
        self.doc_data = response.data.sequences;
        self.renderData();
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
    renderData: function(){
      // Рендерит данные для отображения
      // console.log("Docs: ", this.doc_data);
      var tStr;
      var rStr;
      var labels;
      var lastOffset;
      var delimeter = " ";
      var tagStart = "<span class='lbl' style='color: #ffffff; background-color: #ff0000;' v-b-tooltip.hover title='Label_n'>";
      var tagStop = "<button type='button' class='close'>&times;</button></span>";

      this.data_render = [];

      for (var i = 0; i < this.doc_data.length; i++){
        tStr = this.doc_data[i].text;
        labels = this.doc_data[i].labels;
        lastOffset = 0;
        rStr = "";
        for (var j = 0; j < labels.length; j++){
          rStr += tStr.substring(lastOffset, labels[j].offset_start)
            + tagStart
            + tStr.substring(labels[j].offset_start, labels[j].offset_stop)
            + tagStop;
          lastOffset = labels[j].offset_stop
          // labels[j].label_id
        }
        if (lastOffset == 0){
          rStr = tStr;
        }else{
          rStr = rStr + tStr.substring(lastOffset);
        }
        this.data_render.push(rStr);
      };
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