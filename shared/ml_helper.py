from rdkit import Chem
import numpy as np

"""
Bitstring Representation:

1. Charge Bitstring (2 bits):
   - [0]: Atom has a negative formal charge.
   - [1]: Atom has a positive formal charge.

2. Hydrogen Count Bitstring (4 bits):
   - [0]: Atom has 0 hydrogens.
   - [1]: Atom has 1 hydrogen.
   - [2]: Atom has 2 hydrogens.
   - [3]: Atom has more than 2 hydrogens.

3. Hybridization Bitstring (3 bits):
   - [0]: Atom is SP hybridized.
   - [1]: Atom is SP2 hybridized.
   - [2]: Atom is SP3 hybridized.

4. Element Bitstring (15 bits):
   - [0]: Alkali metals (e.g., Li, Na, K).
   - [1]: Boron (B).
   - [2]: Carbon (C).
   - [3]: Nitrogen (N).
   - [4]: Oxygen (O).
   - [5]: Fluorine (F).
   - [6]: Magnesium (Mg).
   - [7]: Aluminium (Al).
   - [8]: Silicon (Si).
   - [9]: Phosphorus (P).
   - [10]: Sulfur (S).
   - [11]: Chlorine (Cl).
   - [12]: Bromine (Br).
   - [13]: Iodine (I).
   - [14]: Transition metals (atomic numbers 20–30).

5. Aromaticity Bitstring (2 bit):
   - [0]: Atom is not aromatic.
   - [1]: Atom is aromatic.

6. Adjacency Bitstring (9 bits):
   - [0]: Neighboring carbon has a positive formal charge (C+).
   - [1]: Neighboring carbon has a negative formal charge (C-).
   - [2]: Neighboring carbon has at least one hydrogen (CH).
   - [3]: Neighboring carbon is bonded to an electronegative atom via a single bond (C-EN).
   - [4]: Neighboring carbon is bonded to an electronegative atom via a double bond (C=EN).
   - [5]: Neighboring atom is electronegative (EN).
   - [6]: Neighboring atom is electropositive (EP).
   - [7]: Neighboring carbon has no hydrogens (CH0).
   - [8]: Neighbouring carbon is sp2 or sp hybridized

7. Bond Type Bitstring (3 bits):
   - [0]: Single bond.
   - [1]: Double bond.
   - [2]: Triple bond.

8. Ring Size Bitstring (5 bits):
   - [0]: Atom pair is part of a 3-membered ring.
   - [1]: Atom pair is part of a 4-membered ring.
   - [2]: Atom pair is part of a 5-membered ring.
   - [3]: Atom pair is part of a 6-membered ring.
   - [4]: Atom pair is part of a 7+ membered ring.

Total Bitstring Length:
- Mechanism Type Bitstring: 11 bits
___________________________________
- Charge Bitstring: 3 bits
- Hydrogen Count Bitstring: 4 bits
- Hybridization Bitstring: 3 bits
- Element Bitstring: 15 bits
- Aromaticity Bitstring: 2 bits
- Adjacency Bitstring: 9 bits
_________________________________
Atom Fingerprint Total: 35 bits
_________________________________
35*4 = 140 bits for atoms
- Bond Type Bitstring: 3 bits
- Bond Fingerprint Total: 6 bits
__________________________________
- Ring Size Bitstring: 5 bits

"""

electronegativity_dict = {1: 2.2,
 3: 0.98,
 4: 1.57,
 5: 2.04,
 6: 2.55,
 7: 3.04,
 8: 3.44,
 9: 3.98,
 11: 0.93,
 12: 1.31,
 13: 1.61,
 14: 1.9,
 15: 2.19,
 16: 2.58,
 17: 3.16,
 19: 0.82,
 20: 1.0,
 21: 1.36,
 22: 1.54,
 23: 1.63,
 24: 1.66,
 25: 1.55,
 26: 1.83,
 27: 1.88,
 28: 1.91,
 29: 1.9,
 30: 1.65,
 31: 1.81,
 32: 2.01,
 33: 2.18,
 34: 2.55,
 35: 2.96,
 36: 3.0,
 37: 0.82,
 38: 0.95,
 39: 1.22,
 40: 1.33,
 41: 1.6,
 42: 2.16,
 43: 1.9,
 44: 2.2,
 45: 2.28,
 46: 2.2,
 47: 1.93,
 48: 1.69,
 49: 1.78,
 50: 1.96,
 51: 2.05,
 52: 2.1,
 53: 2.66}

def make_atom_fingerprint(atom, other_atom_idx=None):
    if atom is None:
        return [np.nan] * 36

    # Charge bitstring
    charge_bitstring = [0] * 2
    if atom.GetFormalCharge() < 0:
        charge_bitstring[0] = 1
    elif atom.GetFormalCharge() > 0:
        charge_bitstring[1] = 1

    # H bitstring
    h_number_bitstring = [0] * 4
    if atom.GetTotalNumHs() == 0:
        h_number_bitstring[0] = 1
    elif atom.GetTotalNumHs() == 1:
        h_number_bitstring[1] = 1
    elif atom.GetTotalNumHs() == 2:
        h_number_bitstring[2] = 1
    elif atom.GetTotalNumHs() > 2:
        h_number_bitstring[3] = 1

    # Hybridization bitstring
    hybridization_bitstring = [0] * 3
    if atom.GetHybridization() == Chem.rdchem.HybridizationType.SP:
        hybridization_bitstring[0] = 1
    elif atom.GetHybridization() == Chem.rdchem.HybridizationType.SP2:
        hybridization_bitstring[1] = 1
    elif atom.GetHybridization() == Chem.rdchem.HybridizationType.SP3:
        hybridization_bitstring[2] = 1

    # Element bitstring
    # [AlkMet, B, C, N, O, F, Mg, Al, Si, P, S, Cl, Br, I, Met]
    ptable = Chem.GetPeriodicTable()
    element_bitstring = [0] * 15
    dict_elements = { 5: 1,
                      6: 2,
                      7: 3,
                      8: 4,
                      9: 5,
                      12: 6,
                      13: 7,
                      14: 8,
                      15: 9,
                      16: 10,
                      17: 11,
                      35: 12,
                      53: 13}
    atm_num = atom.GetAtomicNum()
    if atm_num in dict_elements:
        element_bitstring[dict_elements[atm_num]] = 1
    elif ptable.GetNOuterElecs(atm_num) == 1:
        element_bitstring[0] = 1
    elif atm_num <= 30 and atm_num >= 20:
        element_bitstring[14] = 1

    # aromaticity bitstring
    new_mol = Chem.Mol(atom.GetOwningMol())
    Chem.SetAromaticity(new_mol)
    if new_mol.GetAtomWithIdx(atom.GetIdx()).GetIsAromatic():
        aromatic_bits = [0, 1]
    else:
        aromatic_bits = [1, 0]

    # adjacency bitstring
    # TODO: add C(EN)3 for good leaving group
    # [C+, C-, CH0, CH, C-EN, C=EN, EN, EP]

    adjecency_bitstring = [0] * 9
    for a in atom.GetNeighbors():
        if other_atom_idx != None and a.GetIdx() == other_atom_idx:
            continue
        if a.GetAtomicNum() == 6:
            if a.GetFormalCharge() > 0:
                adjecency_bitstring[0] = 1
            if a.GetHybridization() == Chem.rdchem.HybridizationType.SP2 or a.GetHybridization() == Chem.rdchem.HybridizationType.SP:
                adjecency_bitstring[8] = 1
            elif a.GetFormalCharge() < 0:
                adjecency_bitstring[1] = 1
            if a.GetTotalNumHs() > 0:
                adjecency_bitstring[2] = 1
            for a2 in a.GetNeighbors():
                if electronegativity_dict[a2.GetAtomicNum()] > 2.55:
                    for b in a.GetBonds():
                        if b.GetOtherAtom(a).GetIdx() == a2.GetIdx():
                            if b.GetBondTypeAsDouble() == 1:
                                adjecency_bitstring[3] = 1
                            elif b.GetBondTypeAsDouble() >= 2:
                                adjecency_bitstring[4] = 1
        elif electronegativity_dict[a.GetAtomicNum()] > 2.55:
            adjecency_bitstring[5] = 1
        elif electronegativity_dict[a.GetAtomicNum()] < 2.05:
            adjecency_bitstring[6] = 1

    three_membered_ring_bitstring = [0] * 1
    if atom.IsInRingSize(3):
        three_membered_ring_bitstring[0] = 1

 

    total_bit_string = charge_bitstring + h_number_bitstring + hybridization_bitstring + element_bitstring + aromatic_bits + adjecency_bitstring + three_membered_ring_bitstring
    return total_bit_string

def make_bond_fingerprint(bond):
    # bond type bitstring
    # [single, double, triple]
    bond_type_bitstring = [0] * 4
    if not bond:
        return bond_type_bitstring
    if bond.GetBondTypeAsDouble() == 1:
        bond_type_bitstring[0] = 1
    elif bond.GetBondTypeAsDouble() == 2:
        bond_type_bitstring[1] = 1
    elif bond.GetBondTypeAsDouble() == 3:
        bond_type_bitstring[2] = 1
    return bond_type_bitstring


def new_bond_fingerprint(mol, a1_idx, a2_idx):
    if a1_idx == None or a2_idx is None:
        return [np.nan] * 5
    a1 = mol.GetAtomWithIdx(a1_idx)
    a2 = mol.GetAtomWithIdx(a2_idx)
    # ring size bitstring
    # [3, 4, 5, 6, 7+]
    ring_size_bitstring = [np.nan] * 5
    fragments = Chem.GetMolFrags(mol)
    for f in fragments:
        if a1.GetIdx() in f and a2.GetIdx() in f:
            if a1.GetIdx() == a2.GetIdx():
                continue
            try:
                len_path = len(Chem.GetShortestPath(mol, a1.GetIdx(), a2.GetIdx()))
            except:
                print("Error in calculating shortest path")
                continue
            if len_path == 3:
                ring_size_bitstring[0] = 1
            elif len_path == 4:
                ring_size_bitstring[1] = 1
            elif len_path == 5:
                ring_size_bitstring[2] = 1
            elif len_path == 6:
                ring_size_bitstring[3] = 1
            elif len_path >= 7:
                ring_size_bitstring[4] = 1
    return ring_size_bitstring


def make_fingerprint(sm, mech):
    mech_type = [np.nan] * 11
    mech_type[mech[0]] = 1
    atom_fps = []
    for i in range(1, 5):
        if mech[i] is None:
            atom_fps.append(make_atom_fingerprint(None))
        else:
            if i in [1, 2]:
                atom_fps.append(make_atom_fingerprint(sm.GetAtomWithIdx(mech[i]), mech[i + 2]))
            elif i in [3, 4]:
                atom_fps.append(make_atom_fingerprint(sm.GetAtomWithIdx(mech[i]), mech[i - 2]))
            else:
                atom_fps.append(make_atom_fingerprint(sm.GetAtomWithIdx(mech[i])))
    if mech[3] and mech[1]:
        b1 = make_bond_fingerprint(sm.GetBondBetweenAtoms(mech[1], mech[3]))
    else:
        b1 = [np.nan] * 4
    if mech[4] and mech[2]:
        b2 = make_bond_fingerprint(sm.GetBondBetweenAtoms(mech[2], mech[4]))
    else:
        b2 = [np.nan] * 4
    r = new_bond_fingerprint(sm, mech[1], mech[2])
    sum_finger_print = mech_type + atom_fps[0] + atom_fps[1] + atom_fps[2] + atom_fps[3] + b1 + b2 + r
    return sum_finger_print