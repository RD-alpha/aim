from run_parallel import run_parallel




# --- Initial molecules ---
sm_smiles = "COC(=O)CC(=O)C.NC(N)=O.c1ccccc1C=O.[OH3+]"
end_smiles = "COC(=O)C1=C(C)NC(=O)NC1c1ccccc1.O.O.[OH3+]"

# sm_smiles = "O.[CH2+]C=C(C)CCC=C(C)CCC=C(C)C"
# end_smiles = "CC1=CCC23CC1C(C)(C)C2CCC3C.[OH3+]"


# Nenitzescu
# sm_smiles = "[OH3+].CN\C=C\C(=O)OC.O=C1C=CC(=O)C=C1"
# end_smiles = "O.[OH3+].COC(=O)C1=CN(C)C2=CC=C(O)C=C12"

# gamma-Cadinane
# sm_smiles = "CC(C)=CCCC(C)=CCCC(C)=C[CH2+].O"
# end_smiles = "C=C1CCC(C(C)C)C2=CC(C)CCC12.[OH3+]"
print("Starting SMILES:", sm_smiles)
print("Ending SMILES:", end_smiles)
try:
	run_parallel(sm_smiles, end_smiles, 0)
except Exception as e:
	print(e)
		
