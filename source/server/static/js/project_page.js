new Vue({
  el: "#project-page",
  delimiters: ['${', '}'],
  data: {
    total_docs: 20,
    processed_docs: 8,
    per_page: 5,
    current_page: 1,
    popoverShow: false,
    docs_arr: [

      { id: 1, name: 'test1', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 2, name: 'test2', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 3, name: 'test3', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 4, name: 'test4', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 5, name: 'test5', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 6, name: 'test6', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 7, name: 'test7', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 8, name: 'test8', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 9, name: 'test9', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 10, name: 'test10', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 11, name: 'test11', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 12, name: 'test12', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 13, name: 'test13', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 14, name: 'test14', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 15, name: 'test15', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 16, name: 'test16', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 17, name: 'test17', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 18, name: 'test18', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 19, name: 'test19', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' },
      { id: 20, name: 'test20', description: 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Minus quae, voluptatem repudiandae quaerat amet reiciendis rerum. Doloremque ab, mollitia quia commodi optio iusto unde laborum dolore reiciendis magnam dolor voluptatibus.' }

    ]
  },
  computed: {
    docs () {
      const docs = this.docs_arr
      return docs.slice(
        (this.current_page - 1) * this.per_page,
        this.current_page * this.per_page
      )
    },
    rows() {
      return this.docs_arr.length
    }
  },
  filters: { 
    truncate: function(string, value) {
        return string.substring(0, value) + '...';
    }
  }
});