const tagsArray = [];
const submitTag = $('#add-tag');

$(submitTag).click(e => {
    console.log(e.currentTarget);
});

function addHandler() {
    $('.tag-node').hover((e) => {
      $( e.target ).css({
        "border": "1px solid red"
      });
    $('.tag-node').click((e) => {
      e.preventDefault();
      const tagId = e.currentTarget.getAttribute('name');
      $.ajax({
        url: '/coder_project/variables',
        type: 'POST',
        data: {
          'delete_tag': 'delete_tag',
          'tag_id': tagId,
          'variable_id': $(variable_id_input).val(),
          'project_id': $(project_id_input).val()
        },

        success: function(json) {
          const tagToRemove = $(`[name="${json.tag_id}"]`);
          tagToRemove.remove();
        },
          error: function(xhr,errmsg,err) {
            console.log(xhr,errmsg,err);
          }
      })

    });
    }, (e) => {
        $( e.target ).css({
          "border": "none"
         });
      }
    );
    console.log('handler added');
}

addHandler();