document.addEventListener('DOMContentLoaded', function() {
    const convertButton = document.getElementById('convert-button');
    const chainButton = document.getElementById('chain-button');
    const smilesInput = document.getElementById('smiles-input');
    const resultsContainer = document.getElementById('results-container');
    const historyList = document.getElementById('history-list');
    const clearHistoryButton = document.getElementById('clear-history-button');
    // const saveHistoryButton = document.getElementById('save-history-button');
    const randomSuggestionButton = document.getElementById('random-suggestion-button');
    // const greenDatasetButton = document.getElementById('green-dataset-button');
    //const toggleHistoryButton = document.getElementById('toggle-history-button');
    const historyContainer = document.getElementById('history-container');
    const infoModal = document.getElementById('info-modal');
    const closeModal = document.getElementById('close-modal');
    const confirmationPopup = document.getElementById('confirmation-popup');

     // Show the modal on first load
     infoModal.style.display = 'block';

     // Close the modal when the close button is clicked
     closeModal.addEventListener('click', () => {
         infoModal.style.display = 'none';
     });

    var mechStep = [];
    var nextStep = [];
    var saveMech = false;
    var id = -1;

     // Toggle the visibility of the history container
   // toggleHistoryButton.addEventListener('click', () => {
    //    if (historyContainer.classList.contains('hidden')) {
      //      historyContainer.classList.remove('hidden');
    //        toggleHistoryButton.textContent = '←'; // Change arrow direction
    //    } else {
    //        historyContainer.classList.add('hidden');
    //        toggleHistoryButton.textContent = '→'; // Change arrow direction
     //   }
   // });


    function callProcessMolecule(smiles, cleanup, kekulise) {
            fetch('/process_molecule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ smiles: smiles,
                    cleanup: cleanup,
                    kekulise: kekulise,
                    id: id
                 })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                if (saveMech == true) {
                mechStep.push(nextStep);
                }
                displayResults(data.molecules);
                addHistory(data.history_idx);
            })
            .catch(error => console.error('Error:', error));
        }

    convertButton.addEventListener('click', function() {
        id = -1;
        const smiles = smilesInput.value;
        const cleanup = document.getElementById('cleanup-checkbox').checked;
        const kekulise = document.getElementById('kekulise-checkbox').checked;
        if (smiles) {
            callProcessMolecule(smiles, cleanup, kekulise);
    }
    });

    chainButton.addEventListener('click', function() {
        const smiles = smilesInput.value;
        const cleanup = document.getElementById('cleanup-checkbox').checked;
        const kekulise = document.getElementById('kekulise-checkbox').checked;
        if (id != -1) {
            /* debug statement */
            console.log("id: " + id);
           callProcessMolecule(smiles, cleanup, kekulise);
        }
    });

    clearHistoryButton.addEventListener('click', () => {
        historyList.innerHTML = '';
        fetch('/clear_history', { method: 'POST' });
    });

    function displayResults(molecules) {
        resultsContainer.innerHTML = '';
        saveMech = false;
        const imageChoices = {}; // Object to store user choices for each image
         // Sort molecules so those with predicted == 1 appear first
        const sortedMolecules = Object.values(molecules).sort((a, b) => b.predicted - a.predicted);

        sortedMolecules.forEach(molecule => {
            const imgContainer = document.createElement('div');
            imgContainer.classList.add('image-container');
            const img = document.createElement('img');
            img.src = `/session_file/results/${molecule.image}?_=${Date.now()}`;
            img.alt = molecule.smiles;
            img.classList.add('result-image');
            const molId = molecule.image.match(/mol_(\d+)\.png/)[1];
            img.dataset.molID = molId;
            // Preselect based on prediction
            if (molecule.predicted === 1) {
                img.style.border = '3px solid green';
                imageChoices[molId] = { mechanism: molecule.mechanism, probable: 1 };
            } else {
                img.style.border = '3px solid red';
                imageChoices[molId] = { mechanism: molecule.mechanism, probable: 0 };
            }

            img.addEventListener('click', function() {
                smilesInput.value = molecule.smiles;
                nextStep = molecule.mechanism;
                saveMech = true;
                id = molId;
            });

            // Create button container
            const buttonContainer = document.createElement('div');
            buttonContainer.classList.add('button-container');
            buttonContainer.dataset.molID = molId;

            const text = document.createElement('p');
            text.textContent = molecule.predicted;


            // Add red button
            const redButton = document.createElement('button');
            redButton.classList.add('red-button');
            redButton.addEventListener('click', () => {
                img.style.border = '3px solid red';
                imageChoices[molId] = {mechanism: molecule.mechanism, probable: 0};
            });

            // Add green button
            const greenButton = document.createElement('button');
            greenButton.classList.add('green-button');
            greenButton.addEventListener('click', () => {
                img.style.border = '3px solid green';
                imageChoices[molId] = {mechanism: molecule.mechanism, probable: 1};
            });
            // Add grey button
            const greyButton = document.createElement('button');
            greyButton.classList.add('grey-button');
            greyButton.addEventListener('click', () => {
                img.style.border = 'none';
                imageChoices[molId] = {mechanism: molecule.mechanism, probable: null};
            });

            // Append buttons to the button container
            buttonContainer.appendChild(redButton);
            buttonContainer.appendChild(greenButton);
            buttonContainer.appendChild(greyButton);
            buttonContainer.appendChild(text);

            // Append elements to the container
            imgContainer.appendChild(img);
            imgContainer.appendChild(buttonContainer);
            resultsContainer.appendChild(imgContainer);
        });

        // Add submit button
        const submitButton = document.createElement('button');
        const userNameInput = document.getElementById('contributor-input');
        submitButton.textContent = 'Save training data';
        submitButton.classList.add('submit-button');
        submitButton.addEventListener('click', () => {
            console.log('User choices:', imageChoices);
            fetch('/save_training_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ choices: imageChoices, contributor: userNameInput.value})
            })
            .then(response => {
                if (response.ok) {
                    console.log('Training data saved successfully');
                    
                    confirmationPopup.classList.add('show');
                    setTimeout(() => {
                        confirmationPopup.classList.remove('show');
                    }, 2000); // Hide after 2 seconds
                } else {
                    console.error('Error saving training data');
                }
            })
            .catch(error => console.error('Error:', error));
        });
        resultsContainer.appendChild(submitButton);
    }

    function addHistory(history_idx) {
        const historyImg = document.createElement('img');
        historyImg.src = `/session_file/history/${history_idx}.png?_=${Date.now()}`;
        historyImg.alt = smilesInput.value;
        historyImg.classList.add('history-image');
        historyList.insertBefore(historyImg, historyList.firstChild);
    }

    // TODO: add a button to save the history    
    // saveHistoryButton.addEventListener('click', () => {
    //     console.log(mechStep);
    //     fetch('/save_history', { 
    //         method: 'POST',  
    //         headers: {
    //         'Content-Type': 'application/json'
    //       },
    //       body: JSON.stringify({
    //         mechanism: mechStep
    //       })
    //     });
    //     mechStep = [];
    // });
    /* TODO: add a then statement to catch errors */


    randomSuggestionButton.addEventListener('click', () => {
        fetch('/get_random_suggestion')
            .then(response => response.json())
            .then(data => {
                if (data.suggestion) {
                    smilesInput.value = data.suggestion;
                } else {
                    console.error('No suggestions available');
                }
            })
            .catch(error => console.error('Error:', error));
    });

   

});

    