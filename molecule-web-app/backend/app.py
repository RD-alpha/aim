from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, send_file, render_template # type: ignore
from rdkit import Chem # pyright: ignore[reportMissingImports]
import os
import shutil
import uuid
import tempfile
from rules.rules import run_next_step
from rules.next_step import follow_on
from helper import make_image, save_files_for_display, clear_results, clear_pickles
import pickle
import json
from ml_helper import make_fingerprint
import numpy as np
import random
from xgboost import XGBClassifier # pyright: ignore[reportMissingImports]
from io import BytesIO
import base64

app = Flask(
    __name__,
    static_folder='../frontend',           # Path to your static files
    template_folder='../frontend'          # Path to your HTML files
)
app.secret_key = 'T0rz5wNS1nS1p2mDU7Zg6DmFxnyQM5Gg'

# --- Utilities ---

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.json'))
with open(config_path) as f:
    config = json.load(f)
MODEL_VERSION = config['model_version']


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

    tmp_dir = get_session_temp_dir()

    #save file for history
    history_count = make_image(smiles, tmp_dir)
    clf = XGBClassifier()
    model_path = f'../../models/{MODEL_VERSION}/xg_model.json'
    clf.load_model(model_path)
    
    if id != -1:
        with open('chain/mol_' + str(id) + '.pkl', 'rb') as f:
            chain_mol = pickle.load(f)
        mols, mechs, inp_mol = run_next_step(smiles, kekulise, cleanup, chain_mol)
    else:
        mols, mechs, inp_mol = run_next_step(smiles, kekulise, cleanup)
    
    predictions = []
    follow_on_mols = []
    follow_on_smiles = []
    for i, mol in enumerate(mols):
        fp = make_fingerprint(inp_mol, mechs[i])
        y_pred = clf.predict(np.array(fp).reshape(1, -1))
        predictions.append(int(y_pred[0]))
        if y_pred[0]:
            f_mols, f_smiles = follow_on(mol, mechs[i])[0]
            follow_on_mols = follow_on_mols + f_mols
            follow_on_smiles = follow_on_smiles + f_smiles
    

    #TODO: reimplement that carrying forward of molecules
    #clear_chain()
    clear_results(tmp_dir)
    clear_pickles(tmp_dir)
    save_files_for_display(mols, inp_mol, tmp_dir)
    if follow_on_mols:
        save_files_for_display(follow_on_mols, inp_mol, tmp_dir, prefix="followon_")

    # Load the resulting molecules (assuming they are saved as images)
    molecules = {}
    follow_ons ={}
    # Load decision tree model
    #clf = joblib.load("../../models/v12/xg_model.pkl")
    # Load the model
   
    for filename in os.listdir(os.path.join(tmp_dir, 'results')):
        if filename.endswith('.png') and filename.startswith('mol_'):
            idx = int(filename.split('_')[1].split('.')[0])
            with open(os.path.join(tmp_dir, 'results/products.txt'), 'r') as f:
                line_num = 0
                for line in f:
                    if line_num == idx:
                        result_smiles = line.rstrip()
                    line_num += 1
            fp = make_fingerprint(inp_mol, mechs[idx])
            molecules[idx] = {'image':filename, 'smiles': result_smiles, 'mechanism': mechs[idx], 'predicted': predictions[idx]}
        if filename.endswith('.png') and filename.startswith('followon_'):
            idx = int(filename.split('_')[1].split('.')[0])
            follow_ons[idx] = {'image':filename, 'smiles':follow_on_smiles[idx]}

            
            



    #print(molecules)
    return jsonify({'molecules': molecules, 'history_idx': history_count, 'follow_ons': follow_ons})




@app.route('/clear_history', methods=['POST'])
def clear_history():
    tmp_dir = get_session_temp_dir()
    history_folder = os.path.join(tmp_dir, 'history')
    if os.path.exists(history_folder):
        shutil.rmtree(history_folder)
        os.makedirs(history_folder)
    return jsonify({'message': 'History cleared'})

# TODO: Reimplement this function later

# @app.route('/save_history', methods=['POST'])
# def save_history():
#     backend_dir = os.path.dirname(os.path.abspath(__file__))
#     pickles_folder = os.path.join(backend_dir, 'pickles')
#     reactions_folder = os.path.abspath(os.path.join(root_folder, 'reactions'))
    
#     data = request.get_json()
#     mechanism = data.get('mechanism')
#     #print(mechanism)
#     with open('pickles/mechanism.txt','a') as f:
#         for step in mechanism:
#             for num in step:
#                 f.write(str(num) + " ")
#             f.write("\n")

#     # Find the highest numbered folder in the reactions directory
#     existing_folders = [int(folder) for folder in os.listdir(reactions_folder) if folder.isdigit()]
#     next_folder_number = max(existing_folders, default=0) + 1
#     new_folder = os.path.join(reactions_folder, str(next_folder_number))

#     # Create the new folder
#     os.makedirs(new_folder)

#     # Copy the contents of the pickles folder to the new folder
#     if os.path.exists(pickles_folder):
#         for filename in os.listdir(pickles_folder):
#             source_file = os.path.join(pickles_folder, filename)
#             if os.path.isfile(source_file):
#                 shutil.copy(source_file, new_folder)

#     # Clear the pickles folder
#     if os.path.exists(pickles_folder):
#         shutil.rmtree(pickles_folder)
#         os.makedirs(pickles_folder)
        
#     return jsonify({'message': 'History saved'})

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

@app.route("/whatnext")
def whatnext():
    # Load some existing arrows
    training_folder = os.path.abspath(os.path.join(root_folder, 'training'))
    num_dirs = len([name for name in os.listdir(training_folder) if os.path.isdir(os.path.join(training_folder, name))])
    random_dir = random.randint(1, num_dirs + 1)
    with open(os.path.join(training_folder,f'{random_dir}/sm.pkl'), 'rb') as f:
        sm = pickle.load(f)
    num_arrows = len([fname for fname in os.listdir(os.path.join(training_folder,f'{random_dir}')) if fname.startswith('mol_')])
    random_mol = random.randint(0, num_arrows)
    with open(os.path.join(training_folder, f'{random_dir}/mol_{random_mol}.pkl'), 'rb') as f:
        next_mol = pickle.load(f)
    with open(os.path.join(training_folder, f'{random_dir}/data.json'), 'r') as f:
        j_data = json.load(f)

    img = Chem.Draw.MolToImage(sm, size=(300,300))

    # Convert PIL Image → base64
    buf = BytesIO()
    img.save(buf, format="PNG")
    c_list = []
    for a in next_mol.GetAtoms():
        if a.GetAtomicNum() == 6:
            c_list.append(a.GetIdx())
    drawer = Chem.Draw.rdMolDraw2D.MolDraw2DSVG(300, 300)
    opts = drawer.drawOptions()
    drawer.DrawMolecule(next_mol, highlightAtoms = c_list)
    drawer.FinishDrawing()
    svg_code = drawer.GetDrawingText()
    png_bindata = base64.b64encode(buf.getvalue()).decode("utf-8")

    mech = j_data['choices'][str(random_mol)]['mechanism']
    return render_template("whatnext.html", svg=svg_code, png_bin = png_bindata)

if __name__ == '__main__':
    app.run(debug=True)
