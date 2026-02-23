import csv
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from run_parallel_no_duplicates import run_parallel
import numpy as np


# with open("reaction_subset.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	row = 0
# 	for l in reader:
# 		print("_"*40)
# 		print(f"Processing row {row + 1}")
# 		print(l[0])
# 		line = l[0]
# 		l_s = line.split(">>")
# 		reactant = l_s[0].strip()
# 		product = l_s[1].strip()
# 		try:
# 			row += 1
# 			if row < 40:
# 				continue
# 			run_parallel(reactant, product, str(row))
# 		except Exception as e:
# 			print(e)


total_rxns = 31364

num_sample = 15

line_nums = np.sort(np.random.choice(np.arange(1,total_rxns+1), size=num_sample, replace=False)+1)

# line_nums = [5295]

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
		
