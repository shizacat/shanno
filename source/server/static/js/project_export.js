new Vue({
  el: "#project-export",
  delimiters: ['${', '}'],
  data: {
    format: 'conllup',
    is_process: false,
    st_variant: 'info', //success, danger
    st_value: '---',
    st_show: false,
  },
  methods: {
    download: function(project_id){
      self = this;

      this.is_process = true;
      axios({
        method: 'get',
        url: "/api/project/" + project_id + "/ds_export/",
        params: {
          "exformat": this.format
        },
        responseType: 'arraybuffer'
      })
      .then(function(response){
        const blob = new Blob([response.data]);
        let link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = 'export.zip';
        link.click();
        self.is_process = false;
      })
      .catch(function(error){
        self.is_process = false;
        self.addError(
          "Ошибка: " + error,
          "danger"
        );
      });
    },
    addError: function(msg, variant){
      this.st_variant = variant;
      this.st_value = msg;
      this.st_show = true;
    },
  }
});