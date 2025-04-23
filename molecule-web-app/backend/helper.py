from rdkit import Chem
import os
import shutil
import pickle

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
        file_name = "mol_" + str(file_num)
        try:
            Chem.Draw.MolToFile(mol, "results/" + file_name + ".png")
            with open ("results/products.txt", 'a', encoding='utf-8') as file:
                line = mol_smiles
                file.write(line +"\n")
            with open("chain/" + file_name + ".pkl", 'wb') as f:
                pickle.dump(mol, f)
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

def clear_chain():
    source_folder = os.path.join(backend_dir, 'chain')
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)
        os.makedirs(source_folder)
    return None

def save_pickle(mol):
    source_folder = os.path.join(backend_dir, 'pickles')
    count = 0
    for filename in os.listdir(source_folder):
        if filename.lower().endswith('.pkl'):
            count += 1
    filename = "mol_" + str(count) +".pkl"        
    with open('pickles/' + filename, 'wb') as f:
        pickle.dump(mol, f)
    return None