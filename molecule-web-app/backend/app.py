from flask import Flask, request, jsonify, send_from_directory
from rdkit import Chem
import os
import shutil
import paramiko
from scp import SCPClient
from rules.rules import execute_step
from helper import make_image, save_files_for_display, clear_results

app = Flask(
    __name__,
    static_folder='../frontend',           # Path to your static files
    template_folder='../frontend'          # Path to your HTML files
)

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

    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    #save file for history
    history_count = make_image(smiles)

    # Save the SMILES string to a temporary file
    with open('temp_smiles.txt', 'w') as f:
        f.write(smiles)
    print(smiles)

    mols, mechs = execute_step(smiles, cleanup, kekulise)

    save_files_for_display(mols)

    # Load the resulting molecules (assuming they are saved as images)
    molecules = {}
    for filename in os.listdir('results'):
        if filename.endswith('.png'):
            idx = int(filename.split('_')[1].split('.')[0])
            with open('results/products.txt', 'r') as f:
                line_num = 0
                for line in f:
                    if line_num == idx:
                        result_smiles = line.rstrip()
                    line_num += 1
            molecules[idx] = {'image': 'results/' + filename, 'smiles': result_smiles, 'mechanism': mechs[idx]}
    
    clear_results()

    print(molecules)
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
    reactions_folder = os.path.abspath(os.path.join(backend_dir, '../../reactions'))
    """host = 'vinson.ch.private.cam.ac.uk'
    username = 'rd611'
    key_path = os.path.expanduser('~/.ssh/id_rsa')
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, key_filename=key_path)
    with SCPClient(ssh.get_transport()) as scp:
        scp.put('local_file.txt', remote_path='/rd611/home/Documents/reaction_history/')
    ssh.close()

    if os.path.exists(pickles_folder):
        shutil.rmtree(pickles_folder)
        os.makedirs(pickles_folder) """
    data = request.get_json()
    mechanism = data.get('mechanism')
    print(mechanism)
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


if __name__ == '__main__':
    app.run(debug=True)