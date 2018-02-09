let radioButtons = document.getElementsByName('variable_answer_option');
let optionsWrapper = document.querySelector('.options-wrapper');

let inputData = [];

radioButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        switch ( button.value ) {
            case 'multiple_choice': {
                let previous_multiple_choice_box = document.querySelector('#multiple_choice_box');

               if (previous_multiple_choice_box) {
                   optionsWrapper.removeChild(previous_multiple_choice_box);
               }

               if ( inputData.length > 0 ) {
                   $( inputData ).each((index, input) => {
                       const choiceEntry = $('<div class="choice-input-wrapper">');
                       const removeNode = $('<span class="glyphicon glyphicon-minus remove-choice"></span>');
                       const inputNode =
                            $(`<input 
                                    style="float: left;" 
                                    class="form-control input__answer-style" 
                                    type="text" 
                                    value="${input.value}"
                                    name="${input.name}"
                                    placeholder="${input.placeholder}"
                            />`);

                       $(choiceEntry).append(removeNode);
                       $(choiceEntry).append(inputNode);

                       $(optionsWrapper).append(choiceEntry);
                   });
               }

               const addChoiceElement = $('span.shown');

               if ( inputData.length == 0 ) {
                   choiceNodeInit();
               }

               if ( $(addChoiceElement).length == 0 && inputData.length < 7 ) {
                    addChoiceNode();
               }
               removeChoiceHandler();
               inputData = [];
               break;
            }

            case 'freeform': {
                const answerStyleInputs = $('.input__answer-style');
                answerStyleInputs.each((index, input) => {
                    const inputInfo = {
                        'value': $(input).val(),
                        'name': $(input).attr('name'),
                        'placeholder': $(input).attr('placeholder')
                    };
                    inputData.push(inputInfo);
                });

                while (optionsWrapper.firstChild) {
                   optionsWrapper.removeChild(optionsWrapper.firstChild);
                }
                break;
            }
        }
    })
});

function addChoiceHandler() {
    $('.add-choice').click(e => {
        e.preventDefault();

        const removeNode = $('<span class="glyphicon glyphicon-minus remove-choice"></span>');
        const inputNode = $('<input style="float: left;" class="form-control input__answer-style" type="text" />');

        $(e.currentTarget).css('display', 'none');
        $(e.currentTarget).removeClass('shown');
        $(e.currentTarget).addClass('hidden');
        $(e.currentTarget).parent().append(removeNode);
        $(e.currentTarget).parent().append(inputNode);

        const answerStyleInputs = $('.input__answer-style');

        if ( answerStyleInputs.length < 7 ) {
            addChoiceNode();
        }
        removeChoiceHandler();
        assignInputNames();
    });
}

function removeChoiceHandler() {
    $('.remove-choice').click(e => {
       e.preventDefault();
       $(e.target).parent().remove();

       const addChoiceElement = $('span.shown');

       if ( $(addChoiceElement).length == 0 ) {
           addChoiceNode();
       }

       assignInputNames();
    });
}

function addChoiceNode() {
   const choiceEntry = $('<div class="choice-input-wrapper">');
   const addChoiceButton = $('<span class="glyphicon glyphicon-plus add-choice shown"></span>');

   $(choiceEntry).append(addChoiceButton);
   $(optionsWrapper).append(choiceEntry);
   addChoiceHandler();
}

function assignInputNames() {
    const answerStyleInputs = $('.input__answer-style');

    $(answerStyleInputs).each((index, input) => {
        $(input).attr('name', `variable-choice-${index + 1}`);
        $(input).attr('placeholder', `Choice ${index + 1}`);
    });
}

function choiceNodeInit() {
    const choiceEntry = $('<div class="choice-input-wrapper">');
    const removeNode = $('<span class="glyphicon glyphicon-minus remove-choice"></span>');
    const inputNode = $('<input style="float: left;" class="form-control input__answer-style" type="text" />');

    $(choiceEntry).append(removeNode);
    $(choiceEntry).append(inputNode);
    $(optionsWrapper).append(choiceEntry);

    assignInputNames();
}