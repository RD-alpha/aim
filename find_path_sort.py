# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: aim
#     language: python
#     name: python3
# ---

from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem.rdFMCS import FindMCS
import numpy as np
import csv
import joblib
import sys
import time
from anytree import Node, RenderTree
from shared.ml_helper import make_fingerprint
import helper
import xgboost
import signal
import pickle
import os

sm_node = None

# Save the tree before job timeout
def save_tree(signum, frame):
    print("Terminating safely")
    jobid = os.environ.get("SLURM_JOB_ID", "backup")
    filename = f"{jobid}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(sm_node,f)
    sys.exit(0)

signal.signal(signal.SIGUSR1, save_tree)
signal.signal(signal.SIGTERM, save_tree)

# Load the model
clf = xgboost.XGBClassifier()
clf.load_model('models/v21/xg_model.json')

print('model loaded - print statements working')

sm_smiles = 'C1CCC(C)C(=O)C1.C=CC(=O)C.[OH-]'
end_smiles = 'CC12CCCCC1=CC(=O)CC2.O.[OH-]'
sm = Chem.MolFromSmiles(sm_smiles)
end = Chem.MolFromSmiles(end_smiles)
sm_node = Node("SM", mol=sm)


# +
# Parameters
force_depth = True
depth_limit = 30
boost = 2
resort_limit = 500
force_correct_last_step = False
aromatic = False
# Initialise variables
step_no = 0
product_nodes = []
times_per_layer = []
nodes = [sm_node]
signal_break = False
unique_id = 0
current_max_depth = 0
best_node = None
highest_sim = 0

RDLogger.DisableLog('rdApp.*')
while step_no < depth_limit:
    product_count = 0
    resort_limit = resort_limit*3
    start_t = time.time()
    print(f'step no {step_no}')
    nodes_to_next = []
    for int in nodes:
        if product_count > resort_limit:
            print(f"Resorting nodes at step {step_no} at depth {current_max_depth}")
            break
        similarity = FindMCS([int.mol, end]).numAtoms
        if hasattr(int, 'priority'):
            p_boost = int.priority + int.depth
        else:
            p_boost = 0
        if hasattr(int, 'product'):
            continue
        try:
            product_mols, mechs, mol_inp  = execute_step("Placeholder", True, aromatic, int.mol)
        except Exception as e:
            print(e)
            continue
        for i, product in enumerate(product_mols):
            fp = np.array(make_fingerprint(mol_inp, mechs[i]))
            pred = clf.predict(fp.reshape(1,-1))[0]
            try:
                inchi1 = Chem.MolToInchi(product, options='FixedH')
                inchi2 = Chem.MolToInchi(end, options='FixedH')
            except Exception as e:
                print(f'Error processing product {i}: {e}')
                continue
            if inchi1 == inchi2:
                print('Found the target molecule!')
                print(f'The final step (mol {unique_id}) was predicted: {pred}')
                if force_correct_last_step and pred != 1:
                        continue
                new_node = Node(f"Mol {unique_id}", parent=int, mol=product, mech=mechs[i])
                new_node.priority = -100
                new_node.product = True
                unique_id += 1
                if force_depth and step_no < depth_limit:
                    product_nodes.append(new_node)
                else:  
                    product_nodes.append(new_node)
                    signal_break = True
                break
            elif pred == 1:
                product_count += 1
                new_node = Node(f"Mol {unique_id}", parent=int, mol=product, mech=mechs[i])
                num_MCS = FindMCS([product, end]).numAtoms
                new_node.similarity = num_MCS
                if num_MCS > similarity: # if there is a greater substructure match than the current node
                    new_node.priority = - new_node.depth + num_MCS * boost + p_boost
                    if num_MCS > highest_sim:
                        highest_sim = num_MCS
                        best_node = new_node
                else:
                    new_node.priority = - new_node.depth + p_boost # TODO: consider some decay here
                if new_node.depth > current_max_depth:
                    current_max_depth = new_node.depth
                unique_id += 1
        if signal_break:
            break
    if signal_break:
        print("we breaking")
        break
    nodes = sm_node.leaves
    nodes = sorted(nodes, key=lambda x: x.priority)
    step_no += 1
    end_t = time.time()
    times_per_layer.append(end_t - start_t)

print("search is over")


# -

for i, dur in enumerate(times_per_layer):
    print(f'Layer {i+1} took {dur:.2f} seconds')



def visualise_tree(node):
    mols = [node.mol]
    while node.is_root is False:
        node = node.parent
        mols.append(node.mol)
    mols.reverse()
    return Chem.Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(400, 400), legends=[f"Mol {i}" for i in range(len(mols))])


def visualise_tree_png(node):
    mols = [node.mol]
    while node.is_root is False:
        node = node.parent
        mols.append(node.mol)
    mols.reverse()
    return Chem.Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(700, 700), legends=[f"Mol {i}" for i in range(len(mols))], returnPNG=True)

for pre, fill, node in RenderTree(sm_node):
    print(f"{pre}{node.name} - {Chem.MolToSmiles(node.mol)}")
    #if hasattr(node, 'mech'):
    #    print(f"{pre}Mechanism: {node.mech}")
    #else:
    #    print(f"{pre}Mechanism: None")



