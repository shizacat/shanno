new Vue({
  el: "#project-import",
  delimiters: ['${', '}'],
  data: {
    files: null,
    activeTab: 0,
    format: 'conllup',
    st_variant: 'info', //success, danger
    st_value: '---',
    st_show: false,
  },
  methods: {
    uploadFiles: function(project_id) {
      self = this;

      let fileData = new FormData;
      fileData.append("files", this.files);
      fileData.append("format", this.format);
      axios.put("/api/project/" + project_id + "/ds_import/", 
        fileData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        }
      ).then(function(response) {
        self.addError(
          "Файл успешно обработан",
          "success"
        )
        self.files = null;
      })
      .catch(function(error) {
        self.addError(
          "Получена ошибка: " + error.response.data,
          "danger"
        );
        self.files = null;
      })
    },
    addError: function(msg, variant){
      this.st_variant = variant;
      this.st_value = msg;
      this.st_show = true;
    },
  }
});