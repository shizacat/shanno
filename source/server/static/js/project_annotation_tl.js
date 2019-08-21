new Vue({
  el: "#project-annotaion",
  methods: {
    onNext: function () {
      console.log("next");
      // this.$router.replace("55")
      console.log("this.$route");
      console.log(window.location.href);
      var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?doc=' + 10;
      window.history.pushState(null, null, newurl);
    }
  },
});