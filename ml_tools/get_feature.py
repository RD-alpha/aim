import argparse

def get_feature_name(index):
    """
    Maps a feature index to its corresponding feature name based on the bitstring breakdown.
    """
    # Define the bitstring breakdown
    feature_mapping = [
        # Mechanism Type Bitstring (8 bits)
        ("Mechanism Type Bit", i) for i in range(8)
    ] + [
        # Atom 1 Features (34 bits)
        ("Atom 1 - Charge Bit", i) for i in range(8, 11)
    ] + [
        ("Atom 1 - Hydrogen Count Bit", i) for i in range(11, 15)
    ] + [
        ("Atom 1 - Hybridization Bit", i) for i in range(15, 18)
    ] + [
        ("Atom 1 - Element Bit", i) for i in range(18, 33)
    ] + [
        ("Atom 1 - Aromaticity Bit", 33)
    ] + [
        ("Atom 1 - Adjacency Bit", i) for i in range(34, 42)
    ] + [
        # Atom 2 Features (34 bits)
        ("Atom 2 - Charge Bit", i) for i in range(42, 45)
    ] + [
        ("Atom 2 - Hydrogen Count Bit", i) for i in range(45, 49)
    ] + [
        ("Atom 2 - Hybridization Bit", i) for i in range(49, 52)
    ] + [
        ("Atom 2 - Element Bit", i) for i in range(52, 67)
    ] + [
        ("Atom 2 - Aromaticity Bit", 67)
    ] + [
        ("Atom 2 - Adjacency Bit", i) for i in range(68, 76)
    ] + [
        # Bond 1 Features (3 bits)
        ("Bond 1 - Bond Type Bit", i) for i in range(76, 79)
    ] + [
        # Bond 2 Features (3 bits)
        ("Bond 2 - Bond Type Bit", i) for i in range(79, 82)
    ] + [
        # Ring Size Features (5 bits)
        ("Ring Size Bit", i) for i in range(82, 87)
    ]

    # Find the feature name for the given index
    for feature_name, feature_index in feature_mapping:
        if feature_index == index:
            return feature_name

    return "Unknown Feature"

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get feature name by index")
    parser.add_argument("index", type=int, help="Feature index to retrieve the name for")
    args = parser.parse_args()
    feature_index = args.index  # Replace with the index you want to analyze
    feature_name = get_feature_name(feature_index)
    print(f"Feature at index {feature_index}: {feature_name}")