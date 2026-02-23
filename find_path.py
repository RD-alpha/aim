from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem import rdMolDescriptors
import numpy as np
import csv
import joblib
import sys
import time
from anytree import Node, RenderTree
from rules import run_next_step
from next_step import follow_on
import helper
from ml_helper import make_fingerprint
import xgboost
import os
import pickle
import signal
import gc                                      # <<< NEW

sm_node = None

# --- SLURM + scratch setup ---
jobid = os.environ.get("SLURM_JOB_ID", "backup")
scratch = os.environ.get("SCRATCH", os.getcwd())   # <<< NEW
os.makedirs(scratch, exist_ok=True)                # <<< NEW
filename = os.path.join(scratch, f"{jobid}.pkl")   # <<< CHANGED

last_save = time.time()
save_interval = 3600

# Save the tree before job timeout
def save_tree(signum, frame):
    print("Terminating safely")
    with open(filename, "wb") as f:
        pickle.dump(product_nodes[0], f)
    sys.exit(0)

signal.signal(signal.SIGUSR1, save_tree)
signal.signal(signal.SIGTERM, save_tree)

# Load the model
clf = xgboost.XGBClassifier()
clf.load_model('models/v51/xg_model.json')

print('model loaded - print statements working')

# --- Initial molecules ---
sm_smiles = 'C1CN2CCN1CC2.CC(=O)C=C.CC(=O)'
end_smiles = 'C1CN2CCN1CC2.CC(=O)C(C(O)C)=C'

sm = Chem.MolFromSmiles(sm_smiles)
end = Chem.MolFromSmiles(end_smiles)

f1 = rdMolDescriptors.CalcMolFormula(sm)
f2 = rdMolDescriptors.CalcMolFormula(end)

assert f1 == f2, f"Molecular formula mismatch: {f1} != {f2}"


# Atom-map the starting molecule
for i, atom in enumerate(sm.GetAtoms(), start=1):   # <<< NEW
    atom.SetAtomMapNum(i)

sm_smiles_mapped = Chem.MolToSmiles(sm, canonical=False)  # <<< NEW
sm_node = Node("SM", smiles=sm_smiles_mapped)             # <<< CHANGED

# +
# Parameters
force_depth = False
depth_limit = 6
force_correct_last_step = True
aromatic = False
follow_on_enabled = True 

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
duplicate_count = 0
inchi_keys = set()
last_save = time.time()

inchi2 = Chem.MolToInchi(end, options='/FixedH')
RDLogger.DisableLog('rdApp.*') 

while step_no < depth_limit:
    product_count = 0
    start_t = time.time()
    print(f'step no {step_no + 1}')

    for int in nodes:
        if hasattr(int, 'product'):
            continue

        # Rebuild Mol from SMILES (transient)
        mol = Chem.MolFromSmiles(int.smiles)          # <<< CHANGED

        try:
            product_mols, mechs, mol_inp = run_next_step(
                "Placeholder", aromatic, True, mol
            )
        except Exception:
            continue

        for i, product in enumerate(product_mols):
            fp = np.array(make_fingerprint(mol_inp, mechs[i]))
            pred = clf.predict(fp.reshape(1, -1))[0]

            try:
                inchi1 = Chem.MolToInchi(product, options='/FixedH')
            except Exception as e:
                print(f'Error processing product {i}: {e}')
                continue

            # Atom-map + SMILES for storage
            for j, atom in enumerate(product.GetAtoms(), start=1):  # <<< NEW
                atom.SetAtomMapNum(j)
            prod_smiles = Chem.MolToSmiles(product, canonical=False)  # <<< NEW

            if inchi1 == inchi2:
                print('Found the target molecule!')
                print(f'The final step (mol {unique_id}) was predicted: {pred}')
                if force_correct_last_step and pred != 1:
                    continue

                unique_id += 1
                new_node = Node(
                    f"Mol {unique_id}",
                    parent=int,
                    smiles=prod_smiles,               # <<< CHANGED
                    mech=mechs[i]
                )
                new_node.product = True
                product_nodes.append(new_node)

                if not (force_depth and step_no < depth_limit):
                    signal_break = True
                break

            elif pred == 1:
                unique_id += 1
                new_node = Node(
                    f"Mol {unique_id}",
                    parent=int,
                    smiles=prod_smiles,               # <<< CHANGED
                    mech=mechs[i]
                )

                if follow_on_enabled:
                    try:
                        f_mols, f_smiles = follow_on(product, mechs[i], clf)
                    except:
                        continue
                        #print("issue with follow on mol")
                        #continue

                    for fm in f_mols:
                        try:
                            inchi1 = Chem.MolToInchi(fm, options='/FixedH')
                        except Exception:
                            continue

                        for j, atom in enumerate(fm.GetAtoms(), start=1):  # <<< NEW
                            atom.SetAtomMapNum(j)
                        fm_smiles = Chem.MolToSmiles(fm, canonical=False)  # <<< NEW

                        unique_id += 1
                        f_node = Node(
                            f"Mol {unique_id}",
                            parent=int,
                            smiles=fm_smiles,          # <<< CHANGED
                            mech="follow_on"
                        )

                        if inchi1 == inchi2:
                            print('Found the target molecule!')
                            f_node.product = True
                            product_nodes.append(f_node)

                            if not (force_depth and step_no < depth_limit):
                                signal_break = True
                                break

        if signal_break:
            break

        if not int.children and not hasattr(int, 'product'):
            int.parent = None

        del mol                                   # <<< NEW
        gc.collect()                              # <<< NEW

    if signal_break:
        print("we breaking")
        break

    nodes = sm_node.leaves

    if time.time() - last_save > save_interval:
        with open(filename, "wb") as f:
            pickle.dump(sm_node, f)

        print(f"[Checkpoint] Tree saved to {filename}")

        with open(f'{filename}.txt', 'w') as f:     # <<< CHANGED
            for pre, fill, node in RenderTree(sm_node):
                f.write(f"{pre}{node.name} - {node.smiles}\n")  # <<< CHANGED

        last_save = time.time()

    step_no += 1
    times_per_layer.append(time.time() - start_t)

print("search is over")

for i, dur in enumerate(times_per_layer):
    print(f'Layer {i+1} took {dur:.2f} seconds')

save_tree(None, None)
