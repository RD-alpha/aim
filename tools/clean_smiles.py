#!/usr/bin/env python3

import sys
from rdkit import Chem


def remove_atom_mapping(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")

    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)

    # Preserve input ordering (avoid canonical reordering)
    return Chem.MolToSmiles(mol, canonical=False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python remove_atom_maps.py '<SMILES>'")
        sys.exit(1)

    smiles = sys.argv[1]

    try:
        cleaned = remove_atom_mapping(smiles)
        print(cleaned)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
