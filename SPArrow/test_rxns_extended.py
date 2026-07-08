import csv
from rdkit import Chem

from run_parallel import run_parallel
no_duplicates = True
force_depth = False
depth_limit = 3
follow_on_enabled = True
aromatic = True
screen_charges_enabled = False
hypervalent_enabled = False

#[21146, 29081, 28573, 21408, 20651, 30124, 19006, 24648, 25033, 28241, 30560, 15595, 26348, 21102, 26224]

SUCCESS_INDICES_DCC_CONDENSATION = [29081]


DCC_BYPRODUCT = ".C1CCCCC1NC(=O)NC1CCCCC1"


with open("data/mech-USPTO-31k.csv", "r") as f:
	reader = csv.reader(f)
	row = 0
	for l in reader:
		row += 1
		if row not in SUCCESS_INDICES_DCC_CONDENSATION:
			continue
		print("_" * 40)
		print(f"Processing row {row}")
		print(l[1])
		print(f"Reaction type: {l[2]}")
		line = l[1]
		l_s = line.split(">>")
		reactant = l_s[0].strip()
		product = l_s[1].strip()
		mol = Chem.MolFromSmiles(reactant)
		Chem.RemoveStereochemistry(mol)
		reactant = Chem.MolToSmiles(mol)
		product = l_s[1].strip()

		mol = Chem.MolFromSmiles(product)
		Chem.RemoveStereochemistry(mol)
		product = Chem.MolToSmiles(mol)
		extended_product = product + DCC_BYPRODUCT
		try:
			run_parallel(reactant, extended_product, str(row), no_duplicates, force_depth, depth_limit, follow_on_enabled, aromatic, screen_charges_enabled, hypervalent_enabled)
		except Exception as e:
			print(e)
		
