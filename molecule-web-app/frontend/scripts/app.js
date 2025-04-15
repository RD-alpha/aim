document.addEventListener('DOMContentLoaded', function() {
    const convertButton = document.getElementById('convert-button');
    const smilesInput = document.getElementById('smiles-input');
    const resultsContainer = document.getElementById('results-container');
    const historyList = document.getElementById('history-list');
    const clearHistoryButton = document.getElementById('clear-history-button');

    convertButton.addEventListener('click', function() {
        const smiles = smilesInput.value;
        const cleanup = document.getElementById('cleanup-checkbox').checked;
        if (smiles) {
            fetch('/process_molecule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ smiles: smiles,
                    cleanup: cleanup
                 })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                displayResults(data.molecules);
                addHistory(data.history_idx);
            })
            .catch(error => console.error('Error:', error));
        }
    });

    clearHistoryButton.addEventListener('click', () => {
        historyList.innerHTML = '';
        fetch('/clear_history', { method: 'POST' });
    });

    function displayResults(molecules) {
        resultsContainer.innerHTML = '';
        Object.values(molecules).forEach(molecule => {
            console.log('molecule_here');
            const img = document.createElement('img');
            img.src = molecule.image + "?v=" + new Date().getTime();
            img.alt = molecule.smiles;
            img.classList.add('molecule-image');
            img.addEventListener('click', function() {
                smilesInput.value = molecule.smiles;
            });
            resultsContainer.appendChild(img);
        });
    }

    function addHistory(history_idx) {
        const historyImg = document.createElement('img');
        historyImg.src = "history/" + history_idx.toString() +".png";
        historyImg.alt = smilesInput.value;
        historyImg.classList.add('history-image');
        historyList.appendChild(historyImg);
    }


});