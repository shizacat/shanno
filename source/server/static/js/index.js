new Vue({
	el: "#main-project-page",
	delimiters: ['${', '}'],
	data: {
		projects: [],
	},
	created() {
		this.getAllProjects();
	},
	methods: {
		getAllProjects: function() {
			self = this;

			axios.get("/api/project/")
			.then(function (response) {
				self.projects = response.data;
			})
			.catch(this.addErrorApi);
		}
	}
});