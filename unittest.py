import unittest
from rdkit import Chem
from aim.rules import execute_step

# filepath: /scratch/rd611/aim/test_rules.ipynb

class TestChemicalReactions(unittest.TestCase):
    def test_sn2_reaction(self):
        # SN2 reaction: CH3CH2Br + I- -> CH3CH2I + Br-
        reactant = "CCBr.[I-]"
        expected_products = {"CCI.[Br-]"}
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))

    def test_hydroboration_step_1(self):
        # Hydroboration: BH3 + CH2=CH2 -> CH3CH2BH2
        reactant = "B.C=C"
        expected_products = {"[BH3-]C[CH2+]"}
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))

    def test_hydroboration_step_2(self):
        # Hydroboration: BH3 + CH2=CH2 -> CH3CH2BH2
        reactant = "[BH3-]C[CH2+]"
        expected_products = {"BCC"}
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))
    

    def test_cyanide_addition_to_carbonyl(self):
        # Cyanide addition: CH3C=O + CN- -> CH3C(OH)CN
        # both cyanide and isocyanide products
        reactant = "CC=O.[C-]#N"
        expected_products = {"CC([O-])C#N", "[C-]#[N+]C(C)[O-]"}
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))

    def test_protonation_of_alkene(self):
        # Protonation: CH2=CH2 + H+ -> CH3CH2+
        reactant = "C=C.[H+]"
        expected_products = {"[H]C([CH2+])C", "[H]C[CH+]C"}
        products = execute_step(reactant)
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))

    def test_alpha_deprotonation_of_ketone(self):
        # Alpha deprotonation: CH3C(=O)CH3 + B- -> [CH2-]C(=O)CH3 + BH
        reactant = "CC(=O)C.[OH-]"
        expected_products = {"O.[CH2-]C(C)=O", "CC(C)([O-])O"}
        products = execute_step(reactant)
        expected_products_inchi = {Chem.MolToInchi(mol for mol in expected_products)}
        products = execute_step(reactant)
        product_inchi = {Chem.MolToInchi(mol) for mol in products}
        self.assertTrue(expected_products_inchi.issubset(product_inchi))

if __name__ == "__main__":
    unittest.main()