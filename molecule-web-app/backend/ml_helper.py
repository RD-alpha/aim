from rdkit import Chem

def make_atom_fingerprint(atom):

    # Charge bitstring
    charge_bitstring = [0] * 3
    if atom.GetFormalCharge() < 0:
        charge_bitstring[0] = 1
    elif atom.GetFormalCharge() == 0:
        charge_bitstring[1] = 1
    elif atom.GetFormalCharge() > 0:
        charge_bitstring[2] = 1

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

    # TODO: aromaticity bitstring

    # adjacency bitstring
    # [C+, C-, CH0, CH, C-EN, C=EN, EN, EP]

    total_bit_string = charge_bitstring + h_number_bitstring + hybridization_bitstring + element_bitstring
    return total_bit_string