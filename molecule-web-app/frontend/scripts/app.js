document.addEventListener('DOMContentLoaded', function() {
    const convertButton = document.getElementById('convert-button');
    const smilesInput = document.getElementById('smiles-input');
    const resultsContainer = document.getElementById('results-container');

    convertButton.addEventListener('click', function() {
        const smiles = smilesInput.value;
        if (smiles) {
            fetch('/process_molecule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ smiles: smiles })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                displayResults(data);
            })
            .catch(error => console.error('Error:', error));
        }
    });

    function displayResults(molecules) {
        resultsContainer.innerHTML = '';
        Object.values(molecules).forEach(molecule => {
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
});