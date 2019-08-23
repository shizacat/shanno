new Vue({
  el: "#project-annotaion",
  delimiters: ['${', '}'],
  data: {
    doc_data: []
  },
  computed: {
    doc_id: function(){
      return window.location.href.split("?doc=")[1];
    }
  },
    created() {
    this.getDocSequence();
  },
  methods: {
    onNext: function () {
      console.log("next");
      // this.$router.replace("55")
      console.log("this.$route");
      console.log(window.location.href);
      var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?doc=' + 10;
      window.history.pushState(null, null, newurl);
    },
    getDocSequence: function() {

      axios.get("/api/document/" + this.doc_id + "/")
      .then(response => {
        this.doc_data = response.data.sequences
        console.log(response)
      })
      .catch(function(error) {
        console.log(error)
      });
    }
  }
});