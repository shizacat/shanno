new Vue({
	el: "#project-delete",
	methods: {
		deleteProject: function(project_id) {
			axios.delete("/api/project/" + project_id)
				.then(function (response) {
          console.log(response);
          if(response.status === 204) {
            location.href = '/projects/';
            }
          })
				.catch(function (error) {
        	console.log(error);
        });
		}
	}
});