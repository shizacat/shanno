export default {
  name:'confirm-doc-del',
  props: ['is_open_delete'],
  data: () => ({
    is_open_del: this.is_open_delete
  }),
  methods: {
    deleteDoc: function(doc_id, index) {
      self = this;

      axios.delete(
        "/api/document/" + doc_id + "/",
        {
          headers: {
            'X-CSRFToken': this.$cookies.get('csrftoken')
          }
        }
      )
      .then(function(response){
        self.is_open_del = null
        // self.docs_total -= 1
        // self.docs.splice(index,1)
      })
      .catch(this.addErrorApi);
    },
    closeDelete: function() {
      this.is_open_del = null
    }
  },
  template: `
    <div class="notification is-info" style="margin-bottom: 1rem" v-show="is_open_del == index">
      <p>{% trans "Are you sure you want to delete the document?" %}</p>
      <br>
      <div class="field is-grouped">
        <p class="control">
          <button class="button is-success is-inverted is-outlined is-small" @click="deleteDoc(doc.id, index)">{% trans "Yes" %}</button>
        </p>
        <p class="control">
          <button class="button is-danger is-inverted is-outlined is-small" @click="closeDelete()">{% trans "No" %}</button>
        </p>
       </div>
      </div>
      `
}