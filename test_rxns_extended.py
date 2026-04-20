import csv

from run_parallel import run_parallel
no_duplicates = True
force_depth = True
depth_limit = 4
follow_on_enabled = True
aromatic = False
screen_charges_enabled = False
hypervalent_enabled = False


SUCCESS_INDICES_DCC_CONDENSATION = [
	3678,
	4511,
	14251,
	22081,
	26881,
	28598,
	8007,
	9410,
	20961,
	23511,
	31152,
	4370,
	8451,
	15866,
	16675,
]

DCC_BYPRODUCT = ".C1CCCCC1NC(=O)NC1CCCCC1"


with open("mech-USPTO-31k.csv", "r") as f:
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
		extended_product = product + DCC_BYPRODUCT
		try:
			run_parallel(reactant, extended_product, str(row), no_duplicates, force_depth, depth_limit, follow_on_enabled, aromatic, screen_charges_enabled, hypervalent_enabled)
		except Exception as e:
			print(e)
		
