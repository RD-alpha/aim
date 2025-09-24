from rdkit import Chem
from rules import execute_step
from ml_helper import make_fingerprint
import xgboost
import numpy as np

clf = xgboost.XGBClassifier()
clf.load_model('models/v15/xg_model.json')


def follow_on(next_mol, mech):
    bonds_to_highlight = []
    atoms_to_highlight = []
    accepted_follow_on = []
    execute_step(next_mol)
    if mech[4] is not None:
        pot_source =next_mol.GetAtomWithIdx(mech[4])
        if pot_source.HasProp('source'):
            for a in next_mol.GetAtomWithIdx(mech[4]).GetNeighbors():
                if a.HasProp('sink'):
                    print(a.GetIdx(), a.GetSymbol(), a.GetProp('sink'))
                    atoms_to_highlight.append(a.GetIdx())
                for b in a.GetBonds():
                    if b.HasProp('sink'):
                        bonds_to_highlight.append(b.GetIdx())
                        print(b.GetIdx(), b.GetProp('sink'))
                
    if mech[3] is not None:
        pot_sink =next_mol.GetAtomWithIdx(mech[3])
        if pot_sink.HasProp('sink'):
            for a in next_mol.GetAtomWithIdx(mech[3]).GetNeighbors():
                if a.HasProp('source'):
                    print(a.GetIdx(), a.GetSymbol(), a.GetProp('source'))
                    atoms_to_highlight.append(a.GetIdx())
                for b in a.GetBonds():
                    if b.HasProp('source'):
                        bonds_to_highlight.append(b.GetIdx())
                        print(b.GetIdx(), b.GetProp('source'))


    for a in next_mol.GetAtoms():
        if a.GetIdx() not in atoms_to_highlight + [mech[3], mech[4]]:
            a.ClearProp('source')
            a.ClearProp('sink')
            if a.GetFormalCharge() == 0:
                a.SetNoImplicit(False)
    for b in next_mol.GetBonds():
        if b.GetIdx() not in bonds_to_highlight:
            b.ClearProp('source')
            b.ClearProp('sink')
            b.ClearProp('source_bond_atom')
            b.ClearProp('sink_bond_atom')
            b.ClearProp('source_other_atom')

    try:
        connected_mols, mechanism, mol_inp = execute_step(next_mol)
    except Exception as e:
        print(e)
    for i, product in enumerate(connected_mols):
        fp = np.array(make_fingerprint(mol_inp, mechanism[i]))
        pred = clf.predict(fp.reshape(1,-1))[0]
        if pred:
            accepted_follow_on.append(product)
        print(f'Product {i}, predicted: {pred}')
    
    return accepted_follow_on