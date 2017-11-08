const tagSubmit = document.querySelector('#add-tag');
const tagInput = document.getElementsByName('variable-tag')[0];
const variable_id_input = document.getElementsByName('variable_id')[0];
const project_id_input = document.getElementsByName('project_id')[0];
const tag_wrapper = document.querySelector('.tag-wrapper');

tagSubmit.addEventListener('submit', e => {
    e.preventDefault();

    $.ajax({
        url: '/coder_project/variables',
        type: 'POST',
        data: {
            'variable-tag': $(tagInput).val(),
            'add-tag': 'add-tag',
            'variable_id': $(variable_id_input).val(),
            'project_id': $(project_id_input).val()
        },

        success: function(json) {
            console.log(json, 'this is the json')

            $(tagSubmit).trigger('reset');
            tag_wrapper.innerHTML = '';
            json.tag_data.forEach(tag => {
                const tagString = '\#' + tag.name + ', ';
                const tagNode = $(`<span></span>`).addClass('tag-node').text(tagString);
                $(tagNode).attr('name', tag.id);
                $(tagNode).hover((e) => {
                  $( e.target ).css({
                    "border": "1px solid red"
                  });
                $(tagNode).click((e) => {
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
                $(tag_wrapper).append(tagNode);
            });

            $(variable_id_input).val(json.variable_id);
            $(project_id_input).val(json.project_id);
        },
        error: function(xhr,errmsg,err) {
            console.log(xhr, errmsg, err);
        }
    });
});
