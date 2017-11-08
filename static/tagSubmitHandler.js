const tagSubmit = document.querySelector('#add-tag');
const tagInput = document.getElementsByName('variable-tag')[0];
const variable_id_input = document.getElementsByName('variable_id')[0];
const project_id_input = document.getElementsByName('project_id')[0];
const tag_wrapper = document.querySelector('.tag-wrapper');

tagSubmit.addEventListener('submit', e => {
    e.preventDefault();
    console.log($(variable_id_input).val(), 'trying to print this variable id');
    console.log($(project_id_input).val(), 'trying to print this project id');

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
            let tagString = '';
            json.tag_data.forEach(tag => {
                tagString = tagString + '\#' + tag.name + ', ';
            });
            tag_wrapper.innerHTML = tagString;

            $(variable_id_input).val(json.variable_id);
            $(project_id_input).val(json.project_id);
        },
        error: function(xhr,errmsg,err) {
            console.log(xhr, errmsg, err);
        }
    });
});