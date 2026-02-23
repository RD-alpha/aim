import csv
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from run_parallel_no_duplicates import run_parallel
import numpy as np


line_nums = [3489, 4594, 8818, 22661]


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
		line = l[1]
		l_s = line.split(">>")
		reactant = l_s[0].strip()
		product = l_s[1].strip()
		try:
			run_parallel(reactant, product, str(row))
		except Exception as e:
			print(e)
		
