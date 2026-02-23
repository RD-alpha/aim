from anytree import Node
import pickle

with open('3068.pkl', 'rb') as f:
	a = pickle.load(f)
with open('3068_prod.pkl', 'wb') as f:
	prod = anytree.search.find_by_attr(a, "Mol 19555666", "name")
	pickle.dump(prod, f)

