new Vue({
	 el: "#project-labels",
	 delimiters: ["${", "}"],
	 data () {
	   return {
	     new_label: null
	   };
	 },
	 computed: {
		project_id: function(){
      return window.location.href.split("/")[4];
    }
	 },
	 methods: {
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
      };
      this.getColor(this.new_label);
    },
    postLabel() {
      axios.post("/api/tl_label/", this.new_label)
        .then((response) => {
          console.log(response);
        })
        .catch((error) => {
          console.log(error);
        });
    },
    cancelCreate() {
      this.new_label = null;
    }
	 }
})

