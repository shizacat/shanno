new Vue({
  el: "#project-import",
  delimiters: ['${', '}'],
  data: {
    files: null,
    selected: 100,
    format: "conllup",
    is_loading: false,
    st_variant: "is-info", //success, danger
    st_value: "---",
    st_show: false,
    tab_value: null,
  },
  methods: {
    uploadFiles: function(project_id) {
      self = this;
      if (this.selected == 100){
        self.addError(
          "Не выбран формат", "is-danger"
        );
        return;
      }

      this.is_loading = true;
      let fileData = new FormData;
      fileData.append("files", this.files);
      fileData.append("format", this.selected);
      axios.put(
        "/api/project/" + project_id + "/ds_import/",
        fileData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            "X-CSRFToken": this.$cookies.get("csrftoken")
          }
        }
      ).then(function(response) {
        self.addError(
          "Файл успешно обработан",
          "is-success"
        )
        self.files = null;
        self.is_loading = false
      })
      .catch(function(error) {
        self.addError(
          "Получена ошибка: " + error.response.data,
          "is-danger"
        );
        self.files = null;
        self.is_loading = false
      })
    },
    addError: function(msg, variant){
      this.st_variant = variant;
      this.st_value = msg;
      this.st_show = true;
    },
  }
});