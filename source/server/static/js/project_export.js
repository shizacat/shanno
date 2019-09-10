new Vue({
  el: "#project-export",
  data: {
    format: 'conllup',
  },
  methods: {
    download: function(project_id){
      self = this;
      // window.location.href = "/api/project/" + project_id + "/ds_export/?exformat=" + this.format;

      axios({
        method: 'get',
        url: "/api/project/" + project_id + "/ds_export/",
        params: {
          "exformat": this.format
        },
        responseType: 'arraybuffer'
      })
      .then(function(response){
        const blob = new Blob([response.data])
        let link = document.createElement('a')
        link.href = window.URL.createObjectURL(blob)
        link.download = 'export.zip'
        link.click()
      })
      .catch(function(error){
        console.log("Error", error)
      });
    }
  }
});