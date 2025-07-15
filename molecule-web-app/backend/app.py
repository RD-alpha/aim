from flask import Flask, request, jsonify, send_from_directory
from rdkit import Chem
import os
import shutil
from rules.rules import execute_step
from helper import make_image, save_files_for_display, clear_results, clear_chain
import pickle
import json
import joblib
from ml_helper import make_fingerprint
import numpy as np
import random
from xgboost import XGBClassifier


app = Flask(
    __name__,
    static_folder='../frontend',           # Path to your static files
    template_folder='../frontend'          # Path to your HTML files
)


root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

@app.route('/')
def serve_index():
    return send_from_directory(app.template_folder, 'index.html')  # Serve the HTML

# Optional: Serve static files like JS/CSS
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route('/process_molecule', methods=['POST'])
def process_molecule():
    data = request.json
    smiles = data.get('smiles')
    cleanup = data.get('cleanup')
    kekulise = data.get('kekulise')
    id = data.get('id')

    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    #save file for history
    history_count = make_image(smiles)

    if id != -1:
        with open('chain/mol_' + str(id) + '.pkl', 'rb') as f:
            chain_mol = pickle.load(f)
        mols, mechs, inp_mol = execute_step(smiles, cleanup, kekulise, chain_mol)
    else:
        mols, mechs, inp_mol = execute_step(smiles, cleanup, kekulise)
    clear_chain()
    save_files_for_display(mols)

    # Load the resulting molecules (assuming they are saved as images)
    molecules = {}

    # Load decision tree model
    #clf = joblib.load("../../models/v12/xg_model.pkl")
    # Load the model
    clf = XGBClassifier()
    clf.load_model('../../models/v12/xg_model.json')
    for filename in os.listdir('results'):
        if filename.endswith('.png'):
            idx = int(filename.split('_')[1].split('.')[0])
            with open('results/products.txt', 'r') as f:
                line_num = 0
                for line in f:
                    if line_num == idx:
                        result_smiles = line.rstrip()
                    line_num += 1
            
                fp = make_fingerprint(inp_mol, mechs[idx])
                y_pred = clf.predict(np.array(fp).reshape(1, -1))
            
            molecules[idx] = {'image': 'results/' + filename, 'smiles': result_smiles, 'mechanism': mechs[idx], 'predicted': int(y_pred[0])}
            
    
    clear_results()
    

    #print(molecules)
    return jsonify({'molecules': molecules, 'history_idx': history_count})




@app.route('/clear_history', methods=['POST'])
def clear_history():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    history_folder = os.path.join(backend_dir, 'history')
    target_folder = os.path.abspath(os.path.join(backend_dir, '../frontend/history'))
    if os.path.exists(history_folder):
        shutil.rmtree(history_folder)
        os.makedirs(history_folder)
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
        os.makedirs(target_folder)
    return jsonify({'message': 'History cleared'})

@app.route('/save_history', methods=['POST'])
def save_history():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    pickles_folder = os.path.join(backend_dir, 'pickles')
    reactions_folder = os.path.abspath(os.path.join(root_folder, 'reactions'))
    
    data = request.get_json()
    mechanism = data.get('mechanism')
    #print(mechanism)
    with open('pickles/mechanism.txt','a') as f:
        for step in mechanism:
            for num in step:
                f.write(str(num) + " ")
            f.write("\n")

    # Find the highest numbered folder in the reactions directory
    existing_folders = [int(folder) for folder in os.listdir(reactions_folder) if folder.isdigit()]
    next_folder_number = max(existing_folders, default=0) + 1
    new_folder = os.path.join(reactions_folder, str(next_folder_number))

    # Create the new folder
    os.makedirs(new_folder)

    # Copy the contents of the pickles folder to the new folder
    if os.path.exists(pickles_folder):
        for filename in os.listdir(pickles_folder):
            source_file = os.path.join(pickles_folder, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, new_folder)

    # Clear the pickles folder
    if os.path.exists(pickles_folder):
        shutil.rmtree(pickles_folder)
        os.makedirs(pickles_folder)
        
    return jsonify({'message': 'History saved'})

@app.route('/save_training_data', methods=['POST'])
def save_training_data():
    data = request.get_json()   
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    chain_folder = os.path.join(backend_dir, 'chain')
    training_folder = os.path.abspath(os.path.join(root_folder, 'training'))
    pickles_folder = os.path.abspath(os.path.join(backend_dir, 'pickles'))
    # Find the pickle file with the highest x in the pickles folder by sorting
    highest_file = None
    if os.path.exists(pickles_folder):
        pickle_files = [filename for filename in os.listdir(pickles_folder)]
        sorted_files = sorted(pickle_files, key=lambda f: int(f.split('_')[1].split('.')[0]), reverse=True)
        if sorted_files:
            highest_file = sorted_files[0]
            highest_file_path = os.path.join(pickles_folder, highest_file)

    # Find the highest numbered folder in the training directory
    existing_folders = [int(folder) for folder in os.listdir(training_folder) if folder.isdigit()]
    next_folder_number = max(existing_folders, default=0) + 1
    new_folder = os.path.join(training_folder, str(next_folder_number))

    # Create the new folder
    os.makedirs(new_folder)
    
    # Copy the contents of the chain folder to the new folder
    if os.path.exists(chain_folder):
        for filename in os.listdir(chain_folder):
            source_file = os.path.join(chain_folder, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, new_folder)
                shutil.copy(highest_file_path, os.path.join(new_folder, 'sm.pkl'))
    with open(os.path.join(new_folder, 'data.json'), 'w') as f:
        json.dump(data, f)
    return jsonify({'message': 'Training data saved'})

@app.route('/get_random_suggestion', methods=['GET'])
def get_random_suggestion():
    suggestions_file = os.path.join(root_folder, 'training_suggestions_2.txt')
    try:
        with open(suggestions_file, 'r') as f:
            lines = f.readlines()
        if not lines:
            return jsonify({'error': 'No suggestions available'}), 404

        # Pick a random line
        
        random_line = random.choice(lines).strip()

        # Remove the selected line from the file
        with open(suggestions_file, 'w') as f:
            f.writelines(line for line in lines if line.strip() != random_line)

        return jsonify({'suggestion': random_line})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
