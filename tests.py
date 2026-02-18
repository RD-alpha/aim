from rdkit import Chem
import numpy as np
import csv
import sys
sys.path.append('molecule-web-app/backend/rules')  # replace with your local path
sys.path.append('molecule-web-app/backend')
# Now you can import your module as usual
from rules import execute_step
import helper
from ml_helper import make_fingerprint
smiles_inp = 'CC1[C+]([O-])c2ccccc2OC1(C)[O-].O'
product_mols = execute_step(smiles_inp, True, False, None)
print(product_mols)