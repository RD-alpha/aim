import csv
import multiprocessing

from run_parallel import run_parallel
import numpy as np
from rdkit import Chem


no_duplicates = True
force_depth = False
depth_limit = 3
follow_on_enabled = True
aromatic = True
screen_charges_enabled = False
hypervalent_enabled = False

timeout_seconds = 30 * 60

total_rxns = 31364

num_sample = 10

line_nums = np.sort(np.random.choice(np.arange(1,total_rxns+1), size=num_sample, replace=False)+1)
# 10309 - Paal Knoor time out
# line_nums = [10309]

# line_nums = [1494, 9080, 15309, 16703]

#line_nums = [15205, 23156]

line_nums = [121, 1986, 2611, 8436, 9681, 11051, 16850, 29699, 1272, 10273, 11136, 20892, 23683, 24808, 25361, 27935, 28714, 1047, 10353, 13792, 14612, 25252, 25491, 25689, 2352, 8437, 10644, 13325, 14498, 20370, 21666, 28168, 30143, 9948, 11504, 12885, 14129, 20615, 22123, 5085, 5972, 6368, 7338, 12750, 15035, 15209, 18986, 29806, 276, 6002, 882, 3610, 9688, 9701, 10929, 2010] + [5470, 26608, 8670, 1254, 6658, 16167, 16893, 19778, 25519, 303, 6251, 5312]


def _run_parallel_worker(reactant, product, row_label, no_duplicates, force_depth, depth_limit,
                         follow_on_enabled, aromatic, screen_charges_enabled, hypervalent_enabled,
                         result_queue):
    try:
        run_parallel(reactant, product, row_label, no_duplicates, force_depth, depth_limit,
                     follow_on_enabled, aromatic, screen_charges_enabled, hypervalent_enabled)
        result_queue.put(None)
    except Exception as e:
        result_queue.put(str(e))


if __name__ == "__main__":
    with open("mech-USPTO-31k.csv", 'r') as f:
        reader = csv.reader(f)
        row = 0
        for l in reader:
            row += 1
            if row not in line_nums:
                continue
            print("_"*40)
            print(f"Processing row {row}")
            print(l[1])
            print(f"Reaction type: {l[2]}")
            if l[2] == "Jones_oxidation":
                print("Skipping.. it don't work")
                continue
            line = l[1]
            l_s = line.split(">>")
            reactant = l_s[0].strip().replace(".[Na+]", "").replace("[H+:301]", "[OH3+]").replace("[H+:302]", "[OH3+]").replace("[H+:303]", "[OH3+]")

            mol = Chem.MolFromSmiles(reactant)
            Chem.RemoveStereochemistry(mol)
            reactant = Chem.MolToSmiles(mol)
            product = l_s[1].strip()

            mol = Chem.MolFromSmiles(product)
            Chem.RemoveStereochemistry(mol)
            product = Chem.MolToSmiles(mol)
            try:
                print("Reactant SMILES: ", reactant)
                result_queue = multiprocessing.Queue()
                p = multiprocessing.Process(
                    target=_run_parallel_worker,
                    args=(
                        reactant, product, str(row), no_duplicates, force_depth,
                        depth_limit, follow_on_enabled, aromatic,
                        screen_charges_enabled, hypervalent_enabled,
                        result_queue,
                    ),
                )
                p.start()
                p.join(timeout_seconds)
                if p.is_alive():
                    print(f"Timeout on row {row}, killing process")
                    p.terminate()
                    p.join()
                    continue
                if not result_queue.empty():
                    err = result_queue.get()
                    if err is not None:
                        print(err)
            except Exception as e:
                print(e)
