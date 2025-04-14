from flask import Flask, request, jsonify, send_from_directory
from rdkit import Chem
import os
import shutil
from rules.rules import execute_step, save_files_for_display


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
    
    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    # Save the SMILES string to a temporary file
    with open('temp_smiles.txt', 'w') as f:
        f.write(smiles)
    print(smiles)
    mols = execute_step(smiles)
   
    save_files_for_display(mols)

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    source_folder = os.path.join(backend_dir, 'results')
    target_folder = os.path.join(backend_dir, '../frontend/results')

    # Remove target folder if it exists
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
        print(f"[INFO] Removed existing folder: {target_folder}")

    # Copy folder from source to target
    shutil.copytree(source_folder, target_folder)
    print(f"[INFO] Copied {source_folder} → {target_folder}")


    # Load the resulting molecules (assuming they are saved as images)
    result_images = []
    for filename in os.listdir('results'):
        if filename.endswith('.png'):
            result_images.append('results/'+filename)
    print(result_images)
    return jsonify({'images': result_images})

if __name__ == '__main__':
    app.run(debug=True)