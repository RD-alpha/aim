from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, send_file, render_template # type: ignore
from rdkit import Chem # pyright: ignore[reportMissingImports]
import os
import sys
import shutil
import uuid
import tempfile
import subprocess
root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if root_folder not in sys.path:
    sys.path.insert(0, root_folder)

from shared.rules import run_next_step
from shared.next_step import follow_on
from helper import make_image, save_files_for_display, clear_results, clear_pickles
import pickle
import json
from shared.ml_helper import make_fingerprint
import numpy as np
import random
from xgboost import XGBClassifier # pyright: ignore[reportMissingImports]
from io import BytesIO
import base64
from shared.explain_mechanism_shap import explain

app = Flask(
    __name__,
    static_folder='../frontend',           # Path to your static files
    template_folder='../frontend'          # Path to your HTML files
)
app.secret_key = 'T0rz5wNS1nS1p2mDU7Zg6DmFxnyQM5Gg'

# --- Utilities ---



def get_or_create_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_session_temp_dir():
    session_id = get_or_create_session_id()
    temp_base = tempfile.gettempdir()
    session_dir = os.path.join(temp_base, f"webapp_session_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(os.path.join(session_dir, 'results'), exist_ok=True)
    os.makedirs(os.path.join(session_dir, 'history'), exist_ok=True)
    os.makedirs(os.path.join(session_dir, 'pickles'), exist_ok=True)
    # os.makedirs(os.path.join(session_dir, 'chain'), exist_ok=True)  #
    return session_dir

def cleanup_session_temp_dir():
    session_dir = get_session_temp_dir()
    shutil.rmtree(session_dir, ignore_errors=True)


@app.route('/')
def serve_index():
    return send_from_directory(app.template_folder, 'index.html')  # Serve the HTML

@app.route('/training')
def serve_training():
    return send_from_directory(app.template_folder, 'index.html')

# Optional: Serve static files like JS/CSS
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route('/process_molecule', methods=['POST'])
def process_molecule():
    data = request.json
    smiles = data.get('smiles')
    kekulise = data.get('kekulise')
    id = data.get('id')
    screen_charges_enabled = data.get('screen_charges_enabled', True)
    hypervalent_enabled = data.get('hypervalent_enabled', True)

    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    tmp_dir = get_session_temp_dir()

    #save file for history
    history_count = make_image(smiles, tmp_dir)
    clf = XGBClassifier()
    model_version = session['selected_model']
    model_path = f'../../models/{model_version}/xg_model.json'
    clf.load_model(model_path)
    
    if id != -1:
        with open('chain/mol_' + str(id) + '.pkl', 'rb') as f:
            chain_mol = pickle.load(f)
        mols, mechs, inp_mol, clean_list = run_next_step(smiles, kekulise, chain_mol, screen_charges_enabled, hypervalent_enabled)
    else:
        mols, mechs, inp_mol, clean_list = run_next_step(smiles, kekulise, None, screen_charges_enabled, hypervalent_enabled)
    
    predictions = []
    follow_on_mols = []
    follow_on_smiles = []
    screened_mols = []
    screened_mechs = []
    screened_predictions = []
    for i, mol in enumerate(mols):
        if mechs[i][0] == 11 or mechs[i][0] == "11":
            predictions.append(1)
            # print("Hydride to proton")
            continue
        fp = make_fingerprint(inp_mol, mechs[i])
        y_pred = clf.predict(np.array(fp).reshape(1, -1))
        predictions.append(int(y_pred[0]))
        if screen_charges_enabled:
            clean_parent = i in clean_list
            if clean_parent:
                screened_mols.append(mol)
                screened_mechs.append(mechs[i])
                screened_predictions.append(int(y_pred[0]))
        else:
            clean_parent = True
        if y_pred[0]:
            f_mols, _, _ = follow_on(mol, mechs[i], clf, screen_charges_enabled, hypervalent_enabled, clean_parent)
            follow_on_mols = follow_on_mols + f_mols


    if screen_charges_enabled:
        mols = screened_mols
        mechs = screened_mechs
        predictions = screened_predictions
        
    clear_results(tmp_dir)
    clear_pickles(tmp_dir)
    save_files_for_display(mols, inp_mol, tmp_dir)
    if follow_on_mols:
        save_files_for_display(follow_on_mols, inp_mol, tmp_dir, prefix="followon_")


    molecules = {}
    follow_ons = {}

    for filename in os.listdir(os.path.join(tmp_dir, 'results')):
        if filename.endswith('.png') and filename.startswith('mol_'):
            idx = int(filename.split('_')[1].split('.')[0])
            with open(os.path.join(tmp_dir, 'results/products.txt'), 'r') as f:
                line_num = 0
                for line in f:
                    if line_num == idx:
                        result_smiles = line.rstrip()
                    line_num += 1
            molecules[idx] = {'image':filename, 'smiles': result_smiles, 'mechanism': mechs[idx], 'predicted': predictions[idx]}
        if filename.endswith('.png') and filename.startswith('followon_'):
            idx = int(filename.split('_')[1].split('.')[0])
            follow_ons[idx] = {'image':filename, 'smiles':Chem.MolToSmiles(follow_on_mols[idx])}


    return jsonify({'molecules': molecules, 'history_idx': history_count, 'follow_ons': follow_ons, "session_id": session["session_id"]})




@app.route('/clear_history', methods=['POST'])
def clear_history():
    tmp_dir = get_session_temp_dir()
    history_folder = os.path.join(tmp_dir, 'history')
    if os.path.exists(history_folder):
        shutil.rmtree(history_folder)
        os.makedirs(history_folder)
    return jsonify({'message': 'History cleared'})



@app.route('/save_training_data', methods=['POST'])
def save_training_data():
    tmp_dir = get_session_temp_dir()
    data = request.get_json()   
    training_folder = os.path.abspath(os.path.join(root_folder, 'training_current'))
    pickles_folder = os.path.abspath(os.path.join(tmp_dir, 'pickles'))
   
    # Find the highest numbered folder in the training directory
    existing_folders = [int(folder) for folder in os.listdir(training_folder) if folder.isdigit()]
    next_folder_number = max(existing_folders, default=0) + 1
    new_folder = os.path.join(training_folder, str(next_folder_number))

    # Create the new folder
    os.makedirs(new_folder)
    

    # Copy the contents of the chain folder to the new folder
    if os.path.exists(pickles_folder):
        for filename in os.listdir(pickles_folder):
            source_file = os.path.join(pickles_folder, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, new_folder)
                
    with open(os.path.join(new_folder, 'data.json'), 'w') as f:
        json.dump(data, f)
    return jsonify({'message': 'Training data saved'})

@app.route('/get_random_suggestion', methods=['GET'])
def get_random_suggestion():
    suggestions_file = os.path.join(root_folder, 'retrain.txt')
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
    

@app.route('/session_file/<path:filepath>')
def session_file(filepath):
    session_dir = get_session_temp_dir()
    # Prevent directory traversal attacks
    safe_path = os.path.normpath(filepath)
    abs_file_path = os.path.abspath(os.path.join(session_dir, safe_path))

    # Ensure the requested file is within the session directory
    if not abs_file_path.startswith(session_dir):
        return 'Invalid file path', 400

    if not os.path.exists(abs_file_path):
        return 'File not found', 404

    return send_file(abs_file_path)

# Add to app.py
@app.route('/api/version')
def get_version():
    return jsonify({'model_version': MODEL_VERSION})

@app.route('/api/explain_mechanism_shap', methods=['POST'])
def explain_mechanism_shap():
    data = request.get_json() or {}
    mechanism = data.get('mechanism')
    tmp_dir = get_session_temp_dir()
    if not isinstance(mechanism, list) or len(mechanism) != 5:
        return jsonify({'error': 'Mechanism must be a 5-item list'}), 400

    script_path = os.path.join(root_folder, 'scripts', 'explain_mechanism_shap.py')
    model_version = session['selected_model']
    model_path = os.path.join(root_folder, 'models', model_version, 'xg_model.json')
    mol_path = os.path.join(tmp_dir, 'pickles', 'sm.pkl')
    with open(mol_path, 'rb') as f:
        mol = pickle.load(f)
   
    import io
    from contextlib import redirect_stdout, redirect_stderr

    buf_out = io.StringIO()
    buf_err = io.StringIO()

    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            # call with (mol, mechanism, model_path) if it accepts 3 args, else try (mol, mechanism)
            explain(mol, mechanism, model_path)

    except Exception as exc:

        return jsonify({'error': str(exc)}), 500

    output = (buf_out.getvalue() + "\n" + buf_err.getvalue()).strip()
    return jsonify({'output': output})

@app.route('/update-model', methods=['POST'])
def update_model():
    data = request.get_json()
    new_model = data.get('model')
    
    if not new_model:
        return jsonify({'status': 'error', 'message': 'No model provided'}), 400

    # Save the model choice directly to this specific user's session
    session['selected_model'] = new_model

    return jsonify({'status': 'success', 'current_model': new_model})

@app.route('/get-models', methods=['GET'])
def list_models():
    try:
        # Ensure the directory actually exists
        models_dir = os.path.abspath(os.path.join(root_folder, 'models'))
        if not os.path.exists(models_dir):
            return jsonify({'models': []})
        # List everything in the directory, but filter so ONLY folders are kept
        available_models = [
            directory for directory in os.listdir(models_dir)
            if os.path.isdir(os.path.join(models_dir, directory))
        ]
        
        # Optional: Sort alphabetically
        available_models.sort()

        return jsonify({'models': available_models})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
