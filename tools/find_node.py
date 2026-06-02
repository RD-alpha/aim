from anytree import Node, RenderTree
from anytree.search import find
import pickle
import os

def load_and_visualize_tree(slurm_id, node_id, node_dir="/nodescratch/[somenode]/rd611", save_dir="./" ):
    # Construct the path to the pickle file
    print(len(os.listdir(os.path.join(node_dir, str(slurm_id)))))
    if len(os.listdir(os.path.join(node_dir, str(slurm_id)))) == 1:
        filename = "tempoutput"
        print(f"Loading single file: {filename}")
        pickle_path = os.path.join(node_dir, str(slurm_id), filename)
        
        # Check if the file exists
        if not os.path.exists(pickle_path):
            print(f"Error: Pickle file for SLURM ID {slurm_id} not found at {pickle_path}")
            return None
        
        # Load the pickled tree node
        with open(pickle_path, "rb") as file:
            node = pickle.load(file)
            n = find(node, lambda n: n.name == f"Mol {node_id}")

        with open(f'{filename}.txt', 'w') as f:     # <<< CHANGED
            for pre, fill, node in RenderTree(n):
                f.write(f"{pre}{node.name} - {node.smiles} \n")  # <<< CHANGED
                if hasattr(node, "mech"):
                    f.write(f"{pre}Mechanism: {node.mech}\n")

load_and_visualize_tree(104934, 41, node_dir="/nodescratch/node-0-4/rd611", save_dir="./")