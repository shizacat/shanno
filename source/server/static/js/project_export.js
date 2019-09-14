new Vue({
  el: "#project-export",
  data: {
    format: 'conllup',
    is_process: false,
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
        console.log("Error", error);
      });
    }
  }
});