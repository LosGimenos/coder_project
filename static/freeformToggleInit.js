let radioButtons = document.getElementsByName('variable_answer_option');
let optionsWrapper = document.querySelector('.options-wrapper');

let choiceArray = [];

const createChoice = () => {
    if (choiceArray.length <= 6) {
        const inputName = 'variable-choice-' + (choiceArray.length + 1).toString();
        choiceArray.push(inputName);
    }
};

const renderChoices = () => {
    const nodeArray = [];

    choiceArray.forEach((choice, index) => {
        let choiceName;
        if (choice.name) {
            choiceName = choice.name;
        } else {
            choiceName = choice;
        }

        let choiceValue = storedChoiceValues[index]['value'];

        if (!choiceValue) {
            choiceValue = '';
        }

        const choiceNodeString = `<input class="input-group" type="input" name="${choiceName}" value="${choiceValue}" />`;
        const choiceNode = $(choiceNodeString);
        nodeArray.push(choiceNode);

    });

    nodeArray.forEach((node, index) => {
        let nodeName = choiceArray[index]['name'];

        if (!nodeName) {
            nodeName = choiceArray[index];
        }

        const forLabelString = `<label for=${nodeName}>Choice ${index + 1}</label>`;

        const inputElement = document.getElementsByName(nodeName)[0];
        const labelElement = $(forLabelString);

        if (!inputElement) {
            $(optionsWrapper).append(labelElement);
            $(optionsWrapper).append(node);
        }
    });
}

getOptionValues();
radioButtons.forEach(button => {
    button.addEventListener('click', (e) => {
       if (button.value == 'multiple_choice') {
           let previous_multiple_choice_box;
           choiceArray = storedChoiceValues;

           try {
               previous_multiple_choice_box = $('#multiple_choice_box');
               optionsWrapper.removeChild(previous_multiple_choice_box);
           } catch (err) {
               console.log('Nodes aint here bub')
           }

           const addChoiceButton = $('<button />', {
              text: 'Add Choice',
              click: function (e) {e.preventDefault(); createChoice(); renderChoices()}
           });

           console.log(addChoiceButton)
           const lineBreak = $('<br />');
           $(optionsWrapper).append(addChoiceButton);
           $(optionsWrapper).append(lineBreak);
        } else if (button.value == 'freeform') {
           while (optionsWrapper.firstChild) {
               optionsWrapper.removeChild(optionsWrapper.firstChild);
           }
           choiceArray = [];
        }
    })
});