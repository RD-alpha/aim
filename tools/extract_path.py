
import pickle
from anytree import Node
from rdkit import Chem

p = 'backup.pkl'
node = pickle.load(open(p, 'rb'))
path = []
cur = node
while cur is not None:
    path.append(cur)
    cur = getattr(cur, 'parent', None)
path.reverse()
for i, n in enumerate(path, start=1):
    mech = getattr(n, 'mech', None)
    smiles = getattr(n, 'smiles', '')
    prod = getattr(n, 'product', False)
    print(f"{i}: {n.name} | product={prod} | smiles={smiles}")
    if mech is not None:
        # mech is [code, i, j, k, l] where indices refer to atoms in the PARENT molecule
        parent = n.parent
        if parent is None:
            print(f"  mech: {mech} (no parent to map atom indices)")
            continue
        pmol = Chem.MolFromSmiles(parent.smiles)
        details = []
        for idx in mech[1:]:
            if idx is None:
                details.append(None)
            else:
                try:
                    atom = pmol.GetAtomWithIdx(idx)
                    details.append(f"{atom.GetSymbol()}:{atom.GetAtomMapNum()}")
                except Exception:
                    details.append(f"idx{idx}")
        print(f"  mech: code={mech[0]}, atoms={details}")
