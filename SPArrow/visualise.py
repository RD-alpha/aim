import pickle
import os
from rdkit import Chem
from rdkit.Chem import Draw
import anytree
import sys

def visualise_tree(node):
    mols = [Chem.MolFromSmiles(node.smiles)]
    while node.is_root is False:
        node = node.parent
        mols.append(Chem.MolFromSmiles(node.smiles))
    mols.reverse()
    return Chem.Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(400, 400), legends=[f"Mol {i}" for i in range(len(mols))])

def load_and_visualize_tree(slurm_id, node_dir="/nodescratch/[somenode]/rd611", save_dir="./"):
    # Construct the path to the pickle file
    print(len(os.listdir(os.path.join(node_dir, str(slurm_id)))))
    if len(os.listdir(os.path.join(node_dir, str(slurm_id)))) == 1:
        filename = os.listdir(os.path.join(node_dir, str(slurm_id)))[0]
        print(f"Loading single file: {filename}")
        pickle_path = os.path.join(node_dir, str(slurm_id), filename)
        
        # Check if the file exists
        if not os.path.exists(pickle_path):
            print(f"Error: Pickle file for SLURM ID {slurm_id} not found at {pickle_path}")
            return None
        
        # Load the pickled tree node
        with open(pickle_path, "rb") as file:
            node = pickle.load(file)
            image = visualise_tree(node)
            # Save the image to a file
            image_path = os.path.join(save_dir, f"{slurm_id}.png")
            image.save(image_path)
            print(f"Image saved to {image_path}")
    # Iterate through all .pkl files matching the pattern
    else:
        for filename in os.listdir(os.path.join(node_dir, str(slurm_id))):
            if filename.startswith(str(slurm_id)) and filename.endswith('.pkl'):
                i = filename.split('.')[0].split('_')[1].strip()
                if len(filename.split('_')) == 3:
                    j = filename.split('.')[0].split('_')[2].strip()
                    i = f"{i}_{j}"
                pickle_path = os.path.join(node_dir, str(slurm_id), filename)
                
                # Check if the file exists
                if not os.path.exists(pickle_path):
                    print(f"Error: Pickle file for SLURM ID {slurm_id} not found at {pickle_path}")
                    return None
                
                # Load the pickled tree node
                with open(pickle_path, "rb") as file:
                    node = pickle.load(file)
                    image = visualise_tree(node)
                    # Save the image to a file
                    image_path = os.path.join(save_dir, f"{slurm_id}_{i}.png")
                    image.save(image_path)
                    print(f"Image saved to {image_path}")
    
    return None

# Example usage:


slurm_id = int(sys.argv[1]) if len(sys.argv) > 1 else 13765

try:
    with open(f'old_slurm/slurm-{slurm_id}.out', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "Running on master node:" in line:
                node = line.split(":")[-1].split('.')[0].strip()
                break
except:
    try:
        with open(f'slurm_out/slurm-{slurm_id}.out', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "Running on master node:" in line:
                    node = line.split(":")[-1].split('.')[0].strip()
                    break
    except:
        try:
            with open(f'slurm-{slurm_id}.out', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "Running on master node:" in line:
                        node = line.split(":")[-1].split('.')[0].strip()
                        break
        except:
            print("Could not find slurm output")

node_dir = f"/nodescratch/{node}/rd611"  # Adjust the node directory path if necessary
save_dir = "./images"  # Directory to save the PNG image

# Ensure the save directory exists
os.makedirs(save_dir, exist_ok=True)

image = load_and_visualize_tree(slurm_id, node_dir, save_dir)
