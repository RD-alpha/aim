from flask import Flask, request, jsonify
from rdkit import Chem
import subprocess
import os

app = Flask(__name__)

@app.route('/process_molecule', methods=['POST'])
def process_molecule():
    data = request.json
    smiles = data.get('smiles')
    
    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    # Save the SMILES string to a temporary file
    with open('temp_smiles.txt', 'w') as f:
        f.write(smiles)

    # Execute the Jupyter notebook using nbconvert
    try:
        subprocess.run(['jupyter', 'nbconvert', '--to', 'python', 'rules/rules.ipynb'], check=True)
        subprocess.run(['python', 'rules/rules.py', 'temp_smiles.txt'], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

    # Load the resulting molecules (assuming they are saved as images)
    result_images = []
    for filename in os.listdir('results'):
        if filename.endswith('.png'):
            result_images.append(filename)

    return jsonify({'images': result_images})

if __name__ == '__main__':
    app.run(debug=True)