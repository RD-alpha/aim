from rdkit import Chem
import os
import shutil

backend_dir = os.path.dirname(os.path.abspath(__file__))

def make_image(smiles):
    source_folder = os.path.join(backend_dir, 'history')
    target_folder = os.path.abspath(os.path.join(backend_dir, '../frontend/history'))
    count = 1
    for filename in os.listdir('history'):
        if filename.lower().endswith('.png'):
            count += 1
    mol = Chem.MolFromSmiles(smiles)
    Chem.Draw.MolToFile(mol, source_folder + "/" + str(count) + '.png')
    Chem.Draw.MolToFile(mol, target_folder + "/"+ str(count) + '.png')
    return count

def save_files_for_display(mols):
    file_num = 0
    
    for mol in mols:
        mol_smiles = Chem.MolToSmiles(mol)
        print(mol_smiles)
        Chem.SanitizeMol(mol)
        file_name = "mol_" + str(file_num) +".png"
        try:
            Chem.Draw.MolToFile(mol, "results/" + file_name)
            with open ("results/products.txt", 'a', encoding='utf-8') as file:
                line = mol_smiles
                file.write(line +"\n")
            file_num += 1
        except:
            print('There was an invalid molecule')

    target_folder = os.path.abspath(os.path.join(backend_dir, '../frontend/results'))
    source_folder = os.path.join(backend_dir, 'results')
    # Remove target folder if it exists
    if os.path.exists(target_folder):
        print('it exists')
        shutil.rmtree(target_folder)
        print(f"[INFO] Removed existing folder: {target_folder}")

    # Copy folder from source to target
    shutil.copytree(source_folder, target_folder)
    print(f"[INFO] Copied {source_folder} → {target_folder}")

   
    return None

def clear_results():
    source_folder = os.path.join(backend_dir, 'results')
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)
        os.makedirs(source_folder)
    return None