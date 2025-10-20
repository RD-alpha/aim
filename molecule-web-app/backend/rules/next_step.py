from rdkit import Chem
from .rules import execute_step
from ml_helper import make_fingerprint
import xgboost
import numpy as np
import os
ptable = Chem.GetPeriodicTable()
from .electronegativity import electronegativity

electronegativity_dict = electronegativity()


clf = xgboost.XGBClassifier()
clf.load_model(os.path.join(os.path.abspath('__file__'),'../../../models/v15/xg_model.json'))


def prepare_atoms(atom):
    # Look for hydrides - M-H bond
    if electronegativity_dict[atom.GetAtomicNum()] < 2.05 and atom.GetFormalCharge() < 0 and atom.GetTotalNumHs() > 0:
        atom.SetNumExplicitHs(atom.GetTotalNumHs())
        atom.SetProp('source', 'hydride')

    # Look for lone pairs
    valence_electrons = ptable.GetNOuterElecs(atom.GetAtomicNum())
    lone_electrons = valence_electrons - atom.GetTotalValence() - atom.GetFormalCharge()
    if lone_electrons > 0:
        atom.SetProp('source', 'lone pair')

    if electronegativity_dict[atom.GetAtomicNum()] > 2.55 and atom.GetTotalNumHs() > 0 and atom.GetFormalCharge() >= 0:
        atom.SetProp('sink', 'proton')
    valence_electrons = ptable.GetNOuterElecs(atom.GetAtomicNum())
    lone_electrons = valence_electrons - atom.GetTotalValence() - atom.GetFormalCharge()
    num_bond_electrons = atom.GetTotalValence()*2

    if lone_electrons + num_bond_electrons < 8 and valence_electrons > 2:
        atom.SetProp('sink', 'empty AO')
    # Special case for s block
    if valence_electrons < 3 and lone_electrons + num_bond_electrons < 2:
        atom.SetProp('sink', 'empty AO')

    # The second row p block expansion pack
    if atom.GetAtomicNum() < 17 and atom.GetAtomicNum() > 13 and atom.GetFormalCharge() >= 0 and atom.GetTotalValence() < 6:
        if atom.HasProp('sink') and atom.GetProp('sink') == 'proton':
            pass
        else:
            atom.SetProp('sink', 'hypervalent')

    if atom.HasProp('sink') and atom.GetProp('sink') == 'hypervalent':
        atom.SetProp('sink', 'empty AO')

    exit_loop = False
    if atom.GetAtomicNum() == 6 and atom.GetTotalNumHs() > 0 and atom.GetFormalCharge() > -1:
        for atom2 in atom.GetNeighbors():
            if atom2.GetFormalCharge() > 0:
                atom.SetProp('sink', 'CH')
            for atom3 in atom2.GetNeighbors():
                # this tolerance is too high but allows for elimination reaction
                # could include optional double bond criterion
                if electronegativity_dict[atom3.GetAtomicNum()]>2.55:
                    atom.SetProp('sink', 'CH')
                    exit_loop = True
                    break
            if exit_loop:
                break
    return None

def follow_on(next_mol, mech):
    bonds_to_highlight = []
    atoms_to_highlight = []
    accepted_follow_on = []
    for a in next_mol.GetAtoms():
        a.ClearProp('source')
        a.ClearProp('sink')
        if a.GetFormalCharge() == 0:
            a.SetNoImplicit(False)
    for b in next_mol.GetBonds():
        b.ClearProp('source')
        b.ClearProp('sink')
        b.ClearProp('source_bond_atom')
        b.ClearProp('sink_bond_atom')
        b.ClearProp('source_other_atom')

    for a in mech[1:]:
        if a is not None:
            prepare_atoms(next_mol.GetAtomWithIdx(a))
    
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
