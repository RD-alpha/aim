document.addEventListener('DOMContentLoaded', function() {
    const convertButton = document.getElementById('convert-button');
    const chainButton = document.getElementById('chain-button');
    const smilesInput = document.getElementById('smiles-input');
    const resultsContainer = document.getElementById('results-container');
    const historyList = document.getElementById('history-list');
    const clearHistoryButton = document.getElementById('clear-history-button');
    const saveHistoryButton = document.getElementById('save-history-button');
    var mechStep = [];
    var nextStep = [];
    var saveMech = false;
    var id = -1;

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

        Object.values(molecules).forEach(molecule => {
            const imgContainer = document.createElement('div');
            imgContainer.classList.add('image-container');

            const img = document.createElement('img');
            img.src = molecule.image + "?v=" + new Date().getTime();
            img.alt = molecule.smiles;
            img.classList.add('result-image');
            const molId = molecule.image.match(/mol_(\d+)\.png/)[1];
            img.dataset.molID = molId;;
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

            // Append buttons to the button container
            buttonContainer.appendChild(redButton);
            buttonContainer.appendChild(greenButton);

            // Append elements to the container
            imgContainer.appendChild(img);
            imgContainer.appendChild(buttonContainer);
            resultsContainer.appendChild(imgContainer);
        });

        // Add submit button
        const submitButton = document.createElement('button');
        submitButton.textContent = 'Save training data';
        submitButton.classList.add('submit-button');
        submitButton.addEventListener('click', () => {
            console.log('User choices:', imageChoices);
            fetch('/save_training_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ choices: imageChoices })
            })
            .then(response => {
                if (response.ok) {
                    console.log('Training data saved successfully');
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
        historyImg.src = "history/" + history_idx.toString() + ".png" + "?v=" + new Date().getTime();
        historyImg.alt = smilesInput.value;
        historyImg.classList.add('history-image');
        historyList.appendChild(historyImg);
    }

    saveHistoryButton.addEventListener('click', () => {
        console.log(mechStep);
        fetch('/save_history', { 
            method: 'POST',  
            headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            mechanism: mechStep
          })
        });
        mechStep = [];
    })
    /* TODO: add a then statement to catch errors */

});