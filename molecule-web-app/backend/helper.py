from rdkit import Chem
from rdkit.Chem import Draw
import os
import shutil
import pickle

def make_image(smiles, tmp_dir):
    source_folder = os.path.join(tmp_dir, 'history')
    count = 1
    for filename in os.listdir(source_folder):
        if filename.lower().endswith('.png'):
            count += 1
    mol = Chem.MolFromSmiles(smiles)
    Chem.Draw.MolToFile(mol, source_folder + "/" + str(count) + '.png')

    return count

def save_files_for_display(mols, inp_mol, tmp_dir, prefix = "mol_"):
    source_folder = os.path.join(tmp_dir, 'results')
    pickle_folder = os.path.join(tmp_dir, 'pickles')
    file_num = 0
    
    # Save starting material as a pickle
    with open(os.path.join(pickle_folder, "sm.pkl"), 'wb') as f:
                pickle.dump(inp_mol, f)
    if prefix == 'mol_':
        for mol in mols:
            mol_smiles = Chem.MolToSmiles(mol)
            Chem.SanitizeMol(mol)
            file_name = prefix + str(file_num)
            try:
                Chem.Draw.MolToFile(mol, os.path.join(source_folder, file_name + ".png"))
                with open (os.path.join(source_folder, "products.txt"), 'a', encoding='utf-8') as file:
                    line = mol_smiles
                    file.write(line +"\n")

            # Save history feature is currently on hold
            # Save molecules as pickles to later save for training
                with open(os.path.join(pickle_folder, file_name + ".pkl"), 'wb') as f:
                    pickle.dump(mol, f)
                file_num += 1

            except:
                print('There was an invalid molecule')
    else:
        for mol in mols:
            try:
                file_name = prefix + str(file_num)
                Chem.SanitizeMol(mol)
                Chem.Draw.MolToFile(mol, os.path.join(source_folder, file_name + ".png"))
                file_num += 1
            except:
                print("Error with SMILES:", Chem.MolToSmiles(mol))
    return None

def clear_results(tmp_dir):
    source_folder = os.path.join(tmp_dir, 'results')
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)
        os.makedirs(source_folder)
    return None

def clear_pickles(tmp_dir):
    source_folder = os.path.join(tmp_dir, 'pickles')
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)
        os.makedirs(source_folder)
    return None


def save_pickle(mol, tmp_dir):
    source_folder = os.path.join(tmp_dir, 'pickles')
    count = 0
    for filename in os.listdir(source_folder):
        if filename.lower().endswith('.pkl'):
            count += 1
    filename = "mol_" + str(count) +".pkl"        
    with open('pickles/' + filename, 'wb') as f:
        pickle.dump(mol, f)
    return None
