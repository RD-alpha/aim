import csv

from run_parallel import run_parallel
import numpy as np

no_duplicates = True
force_depth = False
depth_limit = 6
follow_on_enabled = True
aromatic = True
screen_charges_enabled = False
hypervalent_enabled = False


total_rxns = 31364

num_sample = 25

line_nums = np.sort(np.random.choice(np.arange(1,total_rxns+1), size=num_sample, replace=False)+1)

line_nums = [10309, 15309, 16703, 16855, 17732]

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
			run_parallel(reactant, product, str(row), no_duplicates, force_depth, depth_limit, follow_on_enabled, aromatic, screen_charges_enabled, hypervalent_enabled)
		except Exception as e:
			print(e)
		
