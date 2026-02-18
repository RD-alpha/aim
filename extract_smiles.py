from rdkit import Chem
import pickle
import os

# Directory to start searching from
root_dir = "training"
output_file = "retrain.txt"

# Walk through all subdirectories
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Look for sm.pkl in each directory
    if "sm.pkl" in filenames:
        pkl_path = os.path.join(dirpath, "sm.pkl")
        try:
            # Open and read the pickle file
            with open(pkl_path, 'rb') as f:
                m = pickle.load(f)
                smiles = Chem.MolToSmiles(m)
            
            # Append the SMILES to retain.txt
            with open(output_file, 'a') as f:
                f.write(f"{smiles}\n")
                
        except Exception as e:
            print(f"Error processing {pkl_path}: {e}")