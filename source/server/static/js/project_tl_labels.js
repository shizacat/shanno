  new Vue({
	el: "#project-labels",
  delimiters: ["${", "}"],
  data: {
      new_label: null,
      labels: Array,
      active_edit: null
  },
  computed: {
 	  project_id: function(){
      return window.location.href.split("/")[4];
    }
  },
  created() {
    this.getLabels();
  },
  methods: {
  	getLabels() {
      self = this;
  		axios.get("/api/project/" + this.project_id + "/tl_labels_list/")
  			.then(function(response){
  				self.labels = response.data;
          self.labels.reverse();
  			})
  			.catch(function(error){
  				console.log(error);
  			})
  	},
  	getNewColor() {
      let gencolor = Math.floor(Math.random() * 0xFFFFFF).toString(16);
      let randomColor = "#" + ("000000" + gencolor).slice(-6);
      return randomColor;
    },
    getTextColor(hexcolor) {
      let red = parseInt(hexcolor.substr(1, 2), 16);
      let green = parseInt(hexcolor.substr(3, 2), 16);
      let blue = parseInt(hexcolor.substr(5, 2), 16);
      return ((((red * 299) + (green * 587) + (blue * 114)) / 1000) < 128) ? "#ffffff" : "#000000";
    },
    getColor(label) {
      let bg_color = this.getNewColor();
      let text_color = this.getTextColor(bg_color);
      label.color_background = bg_color;
      label.color_text = text_color;
    },
  	createLabel() {
      this.new_label = {
        name: "Новая метка",
        color_background: "",
        color_text: "",
        project: parseInt(this.project_id)
      };
      this.getColor(this.new_label);
    },
    postLabel() {
      self = this;
      axios.post("/api/tl_label/", this.new_label)
        .then(function(response){
          self.cancelCreate();
          self.labels.unshift(response.data);
          console.log(response);
        })
        .catch(function(error){
          console.log(error);
        });
    },
    cancelCreate() {
      this.new_label = null;
    },
    editLabel(label) {
      this.clone_label = Object.assign({}, label);
      this.active_edit = label;
    },
    deleteLabel(label) {
      self = this;
      axios.delete("/api/tl_label/" + label.id)
      	.then(function(){
        	let index = self.labels.indexOf(label);
        	self.labels.splice(index, 1);
        })
        .catch(function(error){
          console.log(error);
        });
    },
    repealEdit(label) {
      this.active_edit = null;
      Object.assign(label, this.clone_label);
    },
    saveEditChanges(label) {
      self = this;
    	this.active_edit = null;
      axios.patch("/api/tl_label/" + label.id + "/", label)
        .then(function(){
					self.labels;
        })
        .catch(function(error){
          console.log(error);
        });
    }
  }
})

