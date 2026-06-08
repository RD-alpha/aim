document.addEventListener('DOMContentLoaded', function() {
    const isTrainingMode = window.location.pathname.replace(/\/$/, '') === '/training';
    const convertButton = document.getElementById('convert-button');
    const chainButton = document.getElementById('chain-button');
    const smilesInput = document.getElementById('smiles-input');
    const resultsContainer = document.getElementById('results-container');
    const historyList = document.getElementById('history-list');
    const clearHistoryButton = document.getElementById('clear-history-button');
    const randomSuggestionButton = document.getElementById('random-suggestion-button');
    const historyContainer = document.getElementById('history-container');
    const confirmationPopup = document.getElementById('confirmation-popup');
    const errorPopup = document.getElementById('error-popup');
    const ketcherPanel = document.getElementById('ketcher-panel');
    const ketcherPanelBody = document.getElementById('ketcher-panel-body');
    const ketcherFrame = document.getElementById('ketcher-frame');
    const toggleKetcherButton = document.getElementById('toggle-ketcher-button');
    const useDrawnMoleculeButton = document.getElementById('use-drawn-molecule-button');
    const clearDrawnMoleculeButton = document.getElementById('clear-drawn-molecule-button');
    const ketcherStatus = document.getElementById('ketcher-status');
    const shapStatus = document.getElementById('shap-status');
    const shapOutput = document.getElementById('shap-output');
    const shapOutputNatural = document.getElementById('shap-output-natural');
    const dropdown = document.getElementById('model-select');

    document.querySelectorAll('.training-only').forEach(element => {
        element.hidden = !isTrainingMode;
    });


    var mechStep = [];
    var nextStep = [];
    var saveMech = false;
    var id = -1;
    var ketcherReady = false;

    function showErrorPopup() {
        errorPopup.classList.add('show');
        setTimeout(() => {
            errorPopup.classList.remove('show');
        }, 2000);
    }

    function getKetcher() {
        if (!ketcherFrame.contentWindow || !ketcherFrame.contentWindow.ketcher) {
            return null;
        }

        return ketcherFrame.contentWindow.ketcher;
    }

    function setKetcherStatus(message, isError) {
        ketcherStatus.textContent = message;
        ketcherStatus.classList.toggle('error', Boolean(isError));
    }

    window.addEventListener('message', (event) => {
        if (event.origin !== window.location.origin || !event.data) {
            return;
        }

        if (event.data.type === 'ketcher-ready') {
            ketcherReady = true;
            setKetcherStatus('Drawer ready', false);
        }

        if (event.data.type === 'ketcher-error') {
            ketcherReady = false;
            setKetcherStatus(event.data.message || 'Drawer error', true);
        }
    });

    ketcherFrame.addEventListener('load', () => {
        if (!ketcherReady) {
            setKetcherStatus('Loading drawer...', false);
        }
    });

    toggleKetcherButton.addEventListener('click', () => {
        const isHidden = ketcherPanel.classList.toggle('collapsed');
        ketcherPanelBody.hidden = isHidden;
        toggleKetcherButton.textContent = isHidden ? 'Show drawer' : 'Hide drawer';
    });

    useDrawnMoleculeButton.addEventListener('click', async () => {
        const ketcher = getKetcher();

        if (!ketcher) {
            setKetcherStatus('Drawer is not ready', true);
            showErrorPopup();
            return;
        }

        try {
            const smiles = await ketcher.getSmiles();
            if (!smiles) {
                setKetcherStatus('No molecule drawn', true);
                return;
            }

            smilesInput.value = smiles;
            smilesInput.dispatchEvent(new Event('input', { bubbles: true }));
            setKetcherStatus('SMILES copied to input', false);
            id = -1;
        } catch (error) {
            console.error('Ketcher getSmiles error:', error);
            setKetcherStatus('Could not read drawing', true);
            showErrorPopup();
        }
    });

    clearDrawnMoleculeButton.addEventListener('click', async () => {
        const ketcher = getKetcher();

        if (!ketcher) {
            setKetcherStatus('Drawer is not ready', true);
            return;
        }

        try {
            await ketcher.setMolecule('');
            setKetcherStatus('Drawing cleared', false);
        } catch (error) {
            console.error('Ketcher clear error:', error);
            setKetcherStatus('Could not clear drawing', true);
        }
    });

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


    function callProcessMolecule(smiles, kekulise, screenChargesEnabled, hypervalentEnabled) {
            fetch('/process_molecule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ smiles: smiles,
                    kekulise: kekulise,
                    screen_charges_enabled: screenChargesEnabled,
                    hypervalent_enabled: hypervalentEnabled,
                    id: id
                 })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                if (saveMech == true) {
                mechStep.push(nextStep);
                }
                displayResults(data.molecules, data.follow_ons, data.mol_inp_smiles);
                addHistory(data.history_idx);
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorPopup();
            
    });
        }

    function setShapPanel(status, output, isError) {
        shapStatus.textContent = status;
        shapStatus.classList.toggle('error', Boolean(isError));
        shapOutput.textContent = output;
    }
    function setShapPanelNatural(status, output, isError) {
        shapOutputNatural.textContent = output;
    }

    function explainSelectedMolecule(molecule, smiles) {
        setShapPanel('Loading explanation...', 'Running explain_mechanism_shap.py...', false);

        fetch('/api/explain_mechanism_shap', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                smiles: smiles,
                mechanism: molecule.mechanism
            })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) {
                setShapPanel('Explanation failed', data.error || 'Unknown SHAP error', true);
                return;
            }

            setShapPanel('Explanation ready for ' + smiles, data.output || '(no output)', false);
        })
        .catch(error => {
            console.error('SHAP explanation error:', error);
            setShapPanel('Explanation failed', 'Could not run explain_mechanism_shap.py', true);
        });
    
    setShapPanelNatural('Loading explanation...', 'Running explain_mechanism_shap.py...', false);

        fetch('/api/explain_mechanism_shap_llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mechanism: molecule.mechanism
            })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) {
                setShapPanelNatural('Explanation failed', data.error || 'Unknown SHAP error', true);
                return;
            }

            setShapPanelNatural('Explanation ready for ' + smiles, data.output || '(no output)', false);
        })
        .catch(error => {
            console.error('SHAP explanation error:', error);
            setShapPanelNatural('Explanation failed', 'Could not run explain_mechanism_shap.py', true);
        });
    }

    convertButton.addEventListener('click', function() {
        id = -1;
        const smiles = smilesInput.value;
        const kekulise = document.getElementById('kekulise-checkbox').checked;
        const screenChargesEnabled = document.getElementById('screen-charges-checkbox').checked;
        const hypervalentEnabled = document.getElementById('hypervalent-checkbox').checked;
        if (smiles) {
            callProcessMolecule(smiles, kekulise, screenChargesEnabled, hypervalentEnabled);
    }
    });

    chainButton.addEventListener('click', function() {
        const smiles = smilesInput.value;
        const kekulise = document.getElementById('kekulise-checkbox').checked;
        const screenChargesEnabled = document.getElementById('screen-charges-checkbox').checked;
        const hypervalentEnabled = document.getElementById('hypervalent-checkbox').checked;
        if (id != -1) {
            /* debug statement */
            console.log("id: " + id);
           callProcessMolecule(smiles, kekulise, screenChargesEnabled, hypervalentEnabled);
        }
    });

    clearHistoryButton.addEventListener('click', () => {
        historyList.innerHTML = '';
        fetch('/clear_history', { method: 'POST' });
    });

    function displayResults(molecules, follow_ons, input_smiles) {
        resultsContainer.innerHTML = '';
        setShapPanel('Select a molecule to explain', 'No molecule selected.', false);
        saveMech = false;
        const imageChoices = {}; // Object to store user choices for each image
        const imageElements = {}; // Track image elements by molId for bulk actions
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
            imageElements[molId] = img;
            // Show the model prediction in both sites; training mode can override it.
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
                explainSelectedMolecule(molecule, input_smiles);
            });

            
            // Append elements to the container
            imgContainer.appendChild(img);

            if (isTrainingMode) {
                // Create button container
                const buttonContainer = document.createElement('div');
                buttonContainer.classList.add('button-container');
                buttonContainer.dataset.molID = molId;

                const text = document.createElement('p');
                text.textContent = molecule.predicted;


                // Add red button
                const redButton = document.createElement('button');
                redButton.classList.add('red-button');
                redButton.title = 'Mark improbable';
                redButton.addEventListener('click', () => {
                    img.style.border = '3px solid red';
                    imageChoices[molId] = {mechanism: molecule.mechanism, probable: 0};
                });

                // Add green button
                const greenButton = document.createElement('button');
                greenButton.classList.add('green-button');
                greenButton.title = 'Mark probable';
                greenButton.addEventListener('click', () => {
                    img.style.border = '3px solid green';
                    imageChoices[molId] = {mechanism: molecule.mechanism, probable: 1};
                });
                // Add grey button
                const greyButton = document.createElement('button');
                greyButton.classList.add('grey-button');
                greyButton.title = 'Exclude from training save';
                greyButton.addEventListener('click', () => {
                    img.style.border = 'none';
                    imageChoices[molId] = {mechanism: molecule.mechanism, probable: null};
                });

                // Append buttons to the button container
                buttonContainer.appendChild(redButton);
                buttonContainer.appendChild(greenButton);
                buttonContainer.appendChild(greyButton);
                buttonContainer.appendChild(text);
                imgContainer.appendChild(buttonContainer);
            }

            resultsContainer.appendChild(imgContainer);
        });

        const followOns = Object.values(follow_ons);
        followOns.forEach( followOn => {
                const imgContainer = document.createElement('div');
                imgContainer.classList.add('image-container');
                imgContainer.classList.add('follow-on-container');
                const followOnImg = document.createElement('img');
                followOnImg.src = `/session_file/results/${followOn.image}?_=${Date.now()}`;
                followOnImg.alt = "Follow-on product";
                followOnImg.classList.add('result-image');
		        followOnImg.style.border = "3px solid blue";
                imgContainer.appendChild(followOnImg);
                resultsContainer.appendChild(imgContainer);
            followOnImg.addEventListener('click', function() {
                smilesInput.value = followOn.smiles;
        });
        });

        if (!isTrainingMode) {
            return;
        }

        const deselectAllButton = document.createElement('button');
        deselectAllButton.textContent = 'Mark all as not save';
        deselectAllButton.classList.add('bulk-grey-button');
        deselectAllButton.addEventListener('click', () => {
            Object.keys(imageChoices).forEach(molId => {
                imageChoices[molId] = {mechanism: imageChoices[molId].mechanism, probable: null};
                if (imageElements[molId]) {
                    imageElements[molId].style.border = 'none';
                }
            });
        });
        resultsContainer.appendChild(deselectAllButton);

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

    if (isTrainingMode) {
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
    }

    // Fetch the directory list from Flask
    fetch('/get-models')
        .then(response => response.json())
        .then(data => {
            // Clear out the "Loading models..." placeholder
            dropdown.innerHTML = '';

            if (data.models && data.models.length > 0) {
                // Loop through each directory name returned from the backend
                data.models.forEach(modelName => {
                    // Create a new <option> element dynamically
                    const option = document.createElement('option');
                    option.value = modelName;        // What gets sent to the server on change
                    option.textContent = modelName;  // What the user actually sees

                    // Append the option into our dropdown menu
                    dropdown.appendChild(option);
                });
            } else {
                dropdown.innerHTML = '<option disabled>No models found in /models</option>';
            }
        })
        .catch(error => {
            console.error('Error fetching model list:', error);
            dropdown.innerHTML = '<option disabled>Error loading models</option>';
        });


});

// Your existing POST request logic remains the same
function updateModel() {
    const selectedModel = document.getElementById('model-select').value;
    fetch('/update-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
    });
}    
