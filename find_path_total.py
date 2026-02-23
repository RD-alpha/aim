from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem import rdMolDescriptors
import numpy as np
import sys
import time
from anytree import Node, RenderTree
from anytree.search import find
from rules import run_next_step
from next_step import follow_on
from ml_helper import make_fingerprint
import xgboost
import os
import pickle
from multiprocessing import Pool, cpu_count, Manager
import itertools


sm_node = None

# --- SLURM + scratch setup ---
jobid = os.environ.get("SLURM_JOB_ID", "backup")
scratch = os.environ.get("SCRATCH", os.getcwd())   # <<< NEW
os.makedirs(scratch, exist_ok=True)                # <<< NEW
filename = os.path.join(scratch, f"{jobid}")   # <<< CHANGED

# filename = "local_results"

last_save = time.time()
save_interval = 3600

# Save the tree before job timeout
def save_tree(signum, frame):
    print("Terminating safely")
    if product_nodes == []:
        print("No products found, not saving tree")
        sys.exit(0)
    for i, p_n in enumerate(product_nodes):
        with open(f"{filename}_{i}.pkl", "wb") as f:
            pickle.dump(p_n, f)
    sys.exit(0)

# signal.signal(signal.SIGUSR1, save_tree)
# signal.signal(signal.SIGTERM, save_tree)

# Load the model
# clf = xgboost.XGBClassifier()
# clf.load_model('models/v51/xg_model.json')



# --- Initial molecules ---
sm_smiles = "CC(=O)C(O)C(=O)C(O)C(=O)C(O)C(=O)CO.[OH3+]"
end_smiles = ""

print("Starting SMILES:", sm_smiles)
print("Ending SMILES:", end_smiles)

sm = Chem.MolFromSmiles(sm_smiles)
end = Chem.MolFromSmiles(end_smiles)

f1 = rdMolDescriptors.CalcMolFormula(sm)
f2 = rdMolDescriptors.CalcMolFormula(end)

#assert f1 == f2, f"Molecular formula mismatch: {f1} != {f2}"


# Atom-map the starting molecule
for i, atom in enumerate(sm.GetAtoms(), start=1):   # <<< NEW
    atom.SetAtomMapNum(i)

sm_smiles_mapped = Chem.MolToSmiles(sm, canonical=False)  # <<< NEW
sm_node = Node("SM", smiles=sm_smiles_mapped)             # <<< CHANGED

print(sm_node.smiles)

# +
# Parameters
force_depth = True
depth_limit = 3
force_correct_last_step = True
aromatic = True
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

def init_worker():
    global clf
    clf = xgboost.XGBClassifier()
    clf.load_model('models/v71/xg_model.json')
    RDLogger.DisableLog("rdApp.*")


def next_nodes(packed):
    local_id_counter = itertools.count()
    args, found_event = packed
    smiles, name, aromatic, inchi2, force_correct_last_step, follow_on_enabled = args
    results = []
    found_target = False
    if found_event.is_set() and not force_depth:
        return []
    mol = Chem.MolFromSmiles(smiles)
 
    idx_to_mapnum = {}

    for atom in mol.GetAtoms():
        m = atom.GetAtomMapNum()
        if m == 0:
            raise ValueError("All atoms must have atom map numbers")
        i = atom.GetIdx()
        idx_to_mapnum[i] = m
    try:
        product_mols, mechs, mol_inp = run_next_step(
           smiles, aromatic, True, None
        )
    except Exception:
        print("Error in rule application")
        return results
    for i, product in enumerate(product_mols):
        fp = np.array(make_fingerprint(mol_inp, mechs[i]))
        pred = clf.predict(fp.reshape(1, -1))[0]
        try:
            inchi1 = Chem.MolToInchi(product, options='/FixedH')
        except Exception as e:
            print(f'Error processing product {i}: {e}')
            continue
            # Atom-map + SMILES for storage
        for j, atom in enumerate(product.GetAtoms()):  # <<< NEW
            atom.SetAtomMapNum(idx_to_mapnum[j])
        prod_smiles = Chem.MolToSmiles(product, canonical=False)  # <<< NEW

        if inchi1 == inchi2:
            print('Found the target molecule!')
            print(f'Product SMILES: {prod_smiles}')   # <<< CHANGED
            print(f'Inchi: {inchi1}')
            if force_correct_last_step and pred != 1:
                continue
            found_target = True
            found_event.set()
            prod_id = next(local_id_counter)
            results.append({
                    "parent_id": None,
                    "node_id": prod_id,
                    "parent":name,
                    "smiles":prod_smiles,               # <<< CHANGED
                    "mech":mechs[i],
                    "product":True})
            
           
        elif pred == 1:
            prod_id = next(local_id_counter)
            results.append({
                "parent_id": None,
                "node_id": prod_id,
                "parent": name,
                "smiles": prod_smiles,
                "mech": mechs[i],
                "product": False
            })
            

            if follow_on_enabled:
                #print(prod_smiles, mechs[i])
                try:
                    f_mols, f_mechs = follow_on(product, mechs[i], clf)
                except Exception as e:
                    print(e)
                    continue

                for j, fm in enumerate(f_mols):
                    try:
                        inchi_f = Chem.MolToInchi(fm, options='/FixedH')
                    except Exception:
                        print("No Inchi")
                        continue

                    for k, atom in enumerate(fm.GetAtoms()):
                        atom.SetAtomMapNum(idx_to_mapnum[k])
                    fm_smiles = Chem.MolToSmiles(fm, canonical=False)


                    if inchi_f == inchi2:
                        follow_on_id = next(local_id_counter)
                        found_target = True
                        found_event.set()
                        print('Found the target molecule!')
                        print(f'Product SMILES: {prod_smiles}')   # <<< CHANGED
                        print(f'Inchi: {inchi_f}')
                        results.append({
                            "parent_id": prod_id,
                            "node_id": follow_on_id,
                            "parent":name,
                            "smiles":fm_smiles,               # <<< CHANGED
                            "mech": f_mechs[j],
                            "product":True})
                        if not force_depth:
                            break
                        continue
                    follow_on_id = next(local_id_counter)
                    results.append({
                        "parent_id": prod_id,
                        "node_id": follow_on_id,
                        "parent": name,
                        "smiles": fm_smiles,
                        "mech": f_mechs[j],
                        "product": False
                    })

        if found_target and not force_depth:
            break
    # del mol
    return results


while step_no < depth_limit:
    product_count = 0
    start_t = time.time()
    print(f'step no {step_no + 1}')
    
    tasks = [
        (
            int_node.smiles,
            int_node.name,
            aromatic,
            inchi2,
            force_correct_last_step,
            follow_on_enabled
        )
        for int_node in nodes
        if not hasattr(int_node, "product")
    ]

    if __name__ == "__main__":
        with Manager() as manager:
            found_event = manager.Event()
            with Pool(processes=cpu_count(), initializer=init_worker) as pool:
                outputs = pool.map(next_nodes, [(task, found_event) for task in tasks])



    for results in outputs:
        if results == []:
            continue
        temp_nodes = {}
        nodes_with_children = {}
        parent_node_master = find(sm_node, lambda n: n.name == results[0]["parent"])
        for res in results:
            unique_id += 1

            temp_nodes[res["node_id"]] = Node(
                f"Mol {unique_id}",
                smiles=res["smiles"],
                mech=res["mech"],
            )
           
        
        for res in results:
            node = temp_nodes[res["node_id"]]

            if res["parent_id"] is None:
                parent_node = parent_node_master
            else:
                parent_node = temp_nodes[res["parent_id"]]
                nodes_with_children[res["parent_id"]] = temp_nodes[res["parent_id"]]

            node.parent = parent_node

            if res["product"]:
                node.product = True
                product_nodes.append(node)
                if not force_depth:
                    signal_break = True
        
        for res in results:
            node = temp_nodes[res["node_id"]]
            if res["parent_id"] is None:
                if res["node_id"] in nodes_with_children:
                    unique_id += 1
                    tmp_node = Node(f"Mol {unique_id}",
                    smiles=res["smiles"], 
                    mech=res["mech"],
                    parent=parent_node_master)

                parent_node = parent_node_master
            else:
                parent_node = temp_nodes[res["parent_id"]]

            node.parent = parent_node

            if res["product"]:
                node.product = True
                product_nodes.append(node)
                if not force_depth:
                    signal_break = True

    if signal_break:
        break
    
    for int_node in nodes:
        if not int_node.children and not hasattr(int_node, "product"):
            int_node.parent = None

    if not sm_node.leaves:
        print("no more products can be formed, ending search")
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

with open(f'{filename}.txt', 'w') as f:     # <<< CHANGED
        for pre, fill, node in RenderTree(sm_node):
            f.write(f"{pre}{node.name} - {node.smiles} \n")  # <<< CHANGED
            if hasattr(node, "mech"):
                f.write(f" {pre}Mechanism: {node.mech}\n")

#save_tree(None, None)

print("total time", str(time.time() - last_save))
