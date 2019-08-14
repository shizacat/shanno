new Vue({
  el: "#project-import",
  data: {
    files: null,
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
        self.st_variant = "success";
        self.st_value = "Файл успешно обработан";
        self.st_show = true;
        self.files = null;
      })
      .catch(function(error) {
        self.st_variant = "danger";
        self.st_value = "Получена ошибка: " + error;
        self.st_show = true;
      })
    },
  }
});