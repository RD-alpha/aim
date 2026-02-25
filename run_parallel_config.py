from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem import rdMolDescriptors
import numpy as np
import sys
import time
from anytree import Node, RenderTree
from anytree.search import find
from shared.rules import run_next_step
from shared.next_step import follow_on
from shared.ml_helper import make_fingerprint
import xgboost
import os
import pickle
from multiprocessing import Pool, cpu_count, Manager
import itertools
from collections import Counter
import random

# --- SLURM + scratch setup ---
jobid = os.environ.get("SLURM_JOB_ID", "backup")
scratch = os.environ.get("SCRATCH", os.getcwd())   # <<< NEW
os.makedirs(scratch, exist_ok=True)                # <<< NEW
filename = os.path.join(scratch, f"{jobid}")   # <<< CHANGED



def product_subset(reactant, product):
    reactant_counts = Counter(atom.GetSymbol() for atom in reactant.GetAtoms())
    product_counts = Counter(atom.GetSymbol() for atom in product.GetAtoms())

    for element, count in product_counts.items():
        if reactant_counts[element] < count:
            return False
    return True



# filename = "local_results"

last_save = time.time()
save_interval = 3600

# Save the tree before job timeout
def save_tree(signum, frame, job_name, product_nodes):
    print("Terminating safely")
    if product_nodes == []:
        print("No products found, not saving tree")
        #sys.exit(0)
    
    for i, p_n in enumerate(product_nodes):
        with open(f"{filename}_{job_name}_{i}.pkl", "wb") as f:
            pickle.dump(p_n, f)
    #sys.exit(0)

# signal.signal(signal.SIGUSR1, save_tree)
# signal.signal(signal.SIGTERM, save_tree)

# Load the model
# clf = xgboost.XGBClassifier()
# clf.load_model('models/v51/xg_model.json')


def next_nodes(packed):
    unique_mech_count_local = 0
    test_set_mech_count_local = 0
    local_id_counter = itertools.count()
    args, found_event = packed
    smiles, name, aromatic, inchi2, force_depth, force_correct_last_step, follow_on_enabled, fragment = args
    results = []
    found_target = False
    if (found_event.is_set() and not force_depth):
        return (results, (unique_mech_count_local, test_set_mech_count_local))
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
        #print(len(product_mols), "products generated")
    except Exception:
        print("Error in rule application")
        return (results, (unique_mech_count_local, test_set_mech_count_local))
    for i, product in enumerate(product_mols):
        fp = np.array(make_fingerprint(mol_inp, mechs[i]))
        pred = clf.predict(fp.reshape(1, -1))[0]
        found_frag = False
        try:
            inchi1 = Chem.MolToInchi(product, options='/FixedH')
        except Exception as e:
            print(f'Error processing product {i}: {e}')
            continue
        if fragment:
            for m_frag in Chem.GetMolFrags(product, asMols=True):
                try:
                    inchi_frag = Chem.MolToInchi(m_frag, options='/FixedH')
                except Exception:
                    print("No Inchi for fragment")
                    continue
                if inchi_frag == inchi2:
                    found_frag = True
                    print(f"fragment inchi: {inchi_frag}")

            
         # Atom-map + SMILES for storage
        for j, atom in enumerate(product.GetAtoms()):  # <<< NEW
            atom.SetAtomMapNum(idx_to_mapnum[j])
        prod_smiles = Chem.MolToSmiles(product, canonical=False)  # <<< NEW
       

        if inchi1 == inchi2 or found_frag:
            print('Found the target molecule!')
            # print(f'Product SMILES: {prod_smiles}')   # <<< CHANGED
            # print(f'Inchi: {inchi1}')
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
            fp_n = tuple([str(i) for i in fp])
            if fp_n in unique_bitvectors:
                test_set_mech_count_local += 1
            else:
                unique_mech_count_local += 1

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
                    f_mols, f_mechs, f_fps = follow_on(product, mechs[i], clf)
                except Exception as e:
                    print(e)
                    continue

                for j, fm in enumerate(f_mols):
                    found_frag = False
                    if tuple(f_fps[j]) in unique_bitvectors:
                        test_set_mech_count_local += 1
                    else:
                        unique_mech_count_local += 1
                    try:
                        inchi_f = Chem.MolToInchi(fm, options='/FixedH')
                    except Exception:
                        print("No Inchi")
                        continue
                    if fragment:
                        for m_frag in Chem.GetMolFrags(fm, asMols=True):
                            try:
                                inchi_frag = Chem.MolToInchi(m_frag, options='/FixedH')
                            except Exception:
                                print("No Inchi for fragment")
                                continue
                            if inchi_frag == inchi2:
                                found_frag = True
                                # print(f"fragment inchi: {inchi_frag}")
                    
                    

                    for k, atom in enumerate(fm.GetAtoms()):
                        atom.SetAtomMapNum(idx_to_mapnum[k])
                    fm_smiles = Chem.MolToSmiles(fm, canonical=False)


                    if inchi_f == inchi2 or found_frag:
                        follow_on_id = next(local_id_counter)
                        found_target = True
                        found_event.set()
                        print('Found the target molecule!')
                        # print(f'Product SMILES: {prod_smiles}')   # <<< CHANGED
                        # print(f'Inchi: {inchi_f}')
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
    global_var_updates = (unique_mech_count_local, test_set_mech_count_local)
    
    return (results, global_var_updates)





def run_parallel(r_smiles, p_smiles, job_name, depth_limit=3, force_depth=True, force_correct_last_step=True, aromatic=True, follow_on_enabled=True):
    """Run pathfinding from r_smiles to p_smiles.
    
    Args:
        r_smiles: Reactant SMILES
        p_smiles: Product SMILES
        job_name: Job label for output files
        depth_limit: Maximum search depth (default 3)
        force_depth: If True, always search to depth_limit (default True)
        force_correct_last_step: If True, force correct last step (default True)
        aromatic: If True, use aromatic matching (default True)
        follow_on_enabled: If True, enable follow-on reactions (default True)
    """
    
    # Set up
    sm_node = None
    global unique_bitvectors
    unique_bitvectors = set()
    unique_mech_count = 0
    test_set_mech_count = 0
    start_time_total = time.time()

    with open("unique_positive_bitvectors.txt", "r") as f:
        for line in f:
            unique_bitvectors.add(tuple(line.strip().split(',')))


    print(unique_bitvectors)
    # Initialise variables
    step_no = 0
    product_nodes = []
    times_per_layer = []
    signal_break = False
    unique_id = 0
    last_save = time.time()
    fragment = False


    # --- Initial molecules ---
    sm_smiles = r_smiles
    end_smiles = p_smiles

    # print("Starting SMILES:", sm_smiles)
    # print("Ending SMILES:", end_smiles)

    sm = Chem.MolFromSmiles(sm_smiles)
    end = Chem.MolFromSmiles(end_smiles)

    f1 = rdMolDescriptors.CalcMolFormula(sm)
    f2 = rdMolDescriptors.CalcMolFormula(end)

    # if f1 != f2:
    #     subset = product_subset(sm, end)
    #     if not subset:
    #         print(f"Molecular formula mismatch: {f1} != {f2}")
    #         raise ValueError("Molecular formula mismatch, stoichiometry error")
    #     else:
    #         new_end = Chem.GetMolFrags(end, asMols=True)[0]
    #         end = new_end
    #         fragment = True
    #         print("Target is now ", Chem.MolToSmiles(end))
        


    # Atom-map the starting molecule
    for i, atom in enumerate(sm.GetAtoms(), start=1):   # <<< NEW
        atom.SetAtomMapNum(i)

    sm_smiles_mapped = Chem.MolToSmiles(sm, canonical=False)  # <<< NEW
    sm_node = Node("SM", smiles=sm_smiles_mapped)             # <<< CHANGED

    # print(sm_node.smiles)

    nodes = [sm_node]

    

    inchi2 = Chem.MolToInchi(end, options='/FixedH')
    RDLogger.DisableLog('rdApp.*')

    def init_worker():
        global clf
        clf = xgboost.XGBClassifier()
        clf.load_model('models/v81/xg_model.json')
        RDLogger.DisableLog("rdApp.*")



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
                force_depth,
                force_correct_last_step,
                follow_on_enabled, 
                fragment
            )
            for int_node in nodes
            if not hasattr(int_node, "product")
        ]

        with Manager() as manager:
            found_event = manager.Event()
            with Pool(processes=cpu_count(), initializer=init_worker) as pool:
                all_outputs = pool.map(next_nodes, [(task, found_event) for task in tasks])
        
        outputs = [a[0] for a in all_outputs]
        gbl_updates = [a[1] for a in all_outputs]



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

        for update in gbl_updates:
            unique_mech_count += update[0]
            test_set_mech_count += update[1]


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

    with open(f'{filename}_{job_name}.txt', 'w') as f:     # <<< CHANGED
            for pre, fill, node in RenderTree(sm_node):
                f.write(f"{pre}{node.name} - {node.smiles} \n")  # <<< CHANGED
                if hasattr(node, "mech"):
                    f.write(f"{pre}Mechanism: {node.mech}\n")

    save_tree(None, None, job_name, product_nodes)
    print(f"Total time taken: {time.time() - start_time_total:.2f} seconds")
    print(f"Unique mechanisms found: {unique_mech_count}")
    print(f"Test set mechanisms found: {test_set_mech_count}")

    return None
