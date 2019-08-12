new Vue({
  el: "#project-import",
  data(){
  return {
    files: '',
    format: 'conllup'
  }
},
  methods: {
    uploadFiles: function(project_id) {
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
        console.log(response);
      })
      .catch(function(error) {
          console.log("Получена ошибка");
          console.log(error);
      })
    },
    handleFileUpload(){
      this.files = this.$refs.files.files[0];
     }
  }
});