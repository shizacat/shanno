new Vue({
  el: "#project-export",
  data: {
    format: 'conllup',
  },
  methods: {
    download: function(project_id){
      self = this;

      axios({
        method: 'get',
        url: "/api/project/" + project_id + "/ds_export/",
        params: {
          "exformat": this.format
        },
        responseType: 'arraybuffer'
      })
      .then(function(response){
        self.forceFileDownload(response);
      })
      .catch(function(error){
        console.log("Error", error)
      });
    }
  }
});