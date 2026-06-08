from __future__ import annotations

import json
from pathlib import Path

from rdkit import Chem


MECHANISM_TYPE_LABELS = [f"mechanism_type={i}" for i in range(11)]

ATOM_FEATURE_GROUPS: list[tuple[str, list[str]]] = [
    ("charge", ["charge=neg", "charge=pos"]),
    ("hydrogen_count", ["H=0", "H=1", "H=2", "H>2"]),
    ("hybridization", ["hybrid=sp", "hybrid=sp2", "hybrid=sp3"]),
    (
        "element",
        [
            "element=alkali",
            "element=B",
            "element=C",
            "element=N",
            "element=O",
            "element=F",
            "element=Mg",
            "element=Al",
            "element=Si",
            "element=P",
            "element=S",
            "element=Cl",
            "element=Br",
            "element=I",
            "element=transition_metal",
        ],
    ),
    ("aromaticity", ["aromatic"]),
    (
        "adjacency",
        [
            "adjacent=C",
            "adjacent=CH",
            "adjacent=C(sp/sp2)",
            "adjacent=C(aromatic)",
            "adjacent=C-EN",
            "adjacent=C=EN",
            "adjacent=EN",
            "adjacent=EP",
            "adjacent=positive",
            "adjacent=negative"
        ],
    ),
    ("relative_adjacency", ["atom1", "atom2", "atom3", "atom4"]),
    ("ring_membership", ["ring=3"]),
]

BOND_FEATURE_LABELS = ["single", "double", "triple"]
RING_SIZE_FEATURE_LABELS = ["ring=3", "ring=4", "ring=5", "ring=6", "ring>=7"]


def atom_feature_size() -> int:
    return sum(len(labels) for _, labels in ATOM_FEATURE_GROUPS)


def fingerprint_size() -> int:
    return (
        len(MECHANISM_TYPE_LABELS)
        + 4 * atom_feature_size()
        + 2 * len(BOND_FEATURE_LABELS)
        + len(RING_SIZE_FEATURE_LABELS)
    )


def build_section_layout() -> list[dict[str, int | str]]:
    layout: list[dict[str, int | str]] = []
    idx = 0

    def add_section(name: str, size: int) -> None:
        nonlocal idx
        layout.append({"section": name, "start": idx, "size": size, "end": idx + size - 1})
        idx += size

    add_section("mechanism_type", len(MECHANISM_TYPE_LABELS))
    for atom_num in range(1, 5):
        add_section(f"atom{atom_num}", atom_feature_size())
    add_section("bond1", len(BOND_FEATURE_LABELS))
    add_section("bond2", len(BOND_FEATURE_LABELS))
    add_section("new_bond_ring_size", len(RING_SIZE_FEATURE_LABELS))
    return layout


def build_feature_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    idx = 0

    for local_idx, label in enumerate(MECHANISM_TYPE_LABELS):
        entries.append(
            {
                "index": idx,
                "label": label,
                "section": "mechanism_type",
                "group": "mechanism_type",
                "slot": local_idx,
            }
        )
        idx += 1

    for atom_num in range(1, 5):
        for group_name, labels in ATOM_FEATURE_GROUPS:
            for local_idx, label in enumerate(labels):
                entries.append(
                    {
                        "index": idx,
                        "label": f"atom{atom_num}.{label}",
                        "section": f"atom{atom_num}",
                        "group": group_name,
                        "slot": local_idx,
                    }
                )
                idx += 1

    for bond_num in range(1, 3):
        for local_idx, label in enumerate(BOND_FEATURE_LABELS):
            entries.append(
                {
                    "index": idx,
                    "label": f"bond{bond_num}={label}",
                    "section": f"bond{bond_num}",
                    "group": "bond_type",
                    "slot": local_idx,
                }
            )
            idx += 1

    for local_idx, label in enumerate(RING_SIZE_FEATURE_LABELS):
        entries.append(
            {
                "index": idx,
                "label": label,
                "section": "new_bond_ring_size",
                "group": "ring_size",
                "slot": local_idx,
            }
        )
        idx += 1

    return entries


def build_feature_map() -> dict[int, str]:
    return {entry["index"]: entry["label"] for entry in build_feature_entries()}


def build_schema() -> dict[str, object]:
    entries = build_feature_entries()
    return {
        "version": 1,
        "total_features": len(entries),
        "mechanism_type_bits": len(MECHANISM_TYPE_LABELS),
        "atom_feature_bits": atom_feature_size(),
        "bond_feature_bits": len(BOND_FEATURE_LABELS),
        "new_bond_ring_bits": len(RING_SIZE_FEATURE_LABELS),
        "atom_feature_groups": [
            {"name": name, "labels": labels} for name, labels in ATOM_FEATURE_GROUPS
        ],
        "bond_feature_labels": BOND_FEATURE_LABELS,
        "new_bond_ring_labels": RING_SIZE_FEATURE_LABELS,
        "section_layout": build_section_layout(),
        "entries": entries,
    }


def export_schema_json(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_text(json.dumps(build_schema(), indent=2) + "\n")
    return output_path


def validate_schema_against_implementation() -> None:
    from shared.ml_helper import (
        make_atom_fingerprint,
        make_bond_fingerprint,
        make_fingerprint,
        new_bond_fingerprint,
    )

    mol = Chem.MolFromSmiles("CC")
    if mol is None:
        raise RuntimeError("Failed to build validation molecule")

    expected_atom = atom_feature_size()
    actual_atom = len(make_atom_fingerprint(mol.GetAtomWithIdx(0), 1))
    if actual_atom != expected_atom:
        raise ValueError(
            f"Atom fingerprint width mismatch: schema={expected_atom}, implementation={actual_atom}"
        )

    actual_bond = len(make_bond_fingerprint(mol.GetBondBetweenAtoms(0, 1)))
    if actual_bond != len(BOND_FEATURE_LABELS):
        raise ValueError(
            "Bond fingerprint width mismatch: "
            f"schema={len(BOND_FEATURE_LABELS)}, implementation={actual_bond}"
        )

    actual_ring = len(new_bond_fingerprint(mol, 0, 1))
    if actual_ring != len(RING_SIZE_FEATURE_LABELS):
        raise ValueError(
            "New-bond ring fingerprint width mismatch: "
            f"schema={len(RING_SIZE_FEATURE_LABELS)}, implementation={actual_ring}"
        )

    actual_total = len(make_fingerprint(mol, [0, 0, 1, None, None]))
    expected_total = fingerprint_size()
    if actual_total != expected_total:
        raise ValueError(
            f"Total fingerprint width mismatch: schema={expected_total}, implementation={actual_total}"
        )

    entries = build_feature_entries()
    if len(entries) != expected_total:
        raise ValueError(
            f"Feature entry count mismatch: entries={len(entries)}, expected_total={expected_total}"
        )

    for expected_idx, entry in enumerate(entries):
        if entry["index"] != expected_idx:
            raise ValueError(
                f"Feature index mismatch at position {expected_idx}: entry has index={entry['index']}"
            )

    section_layout = build_section_layout()
    entries_by_section: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        entries_by_section.setdefault(str(entry["section"]), []).append(entry)

    for section in section_layout:
        name = str(section["section"])
        start = int(section["start"])
        size = int(section["size"])
        end = int(section["end"])
        section_entries = entries_by_section.get(name, [])

        if len(section_entries) != size:
            raise ValueError(
                f"Section size mismatch for {name}: layout={size}, entries={len(section_entries)}"
            )
        if int(section_entries[0]["index"]) != start:
            raise ValueError(
                f"Section start mismatch for {name}: layout={start}, entries={section_entries[0]['index']}"
            )
        if int(section_entries[-1]["index"]) != end:
            raise ValueError(
                f"Section end mismatch for {name}: layout={end}, entries={section_entries[-1]['index']}"
            )

    # first_labels = {
    #     "mechanism_type": "mechanism_type=0",
    #     "atom1": "atom1.charge=neg",
    #     "atom2": "atom2.charge=neg",
    #     "atom3": "atom3.charge=neg",
    #     "atom4": "atom4.charge=neg",
    #     "bond1": "bond1=single",
    #     "bond2": "bond2=single",
    #     "new_bond_ring_size": "ring=3",
    # }
    # last_labels = {
    #     "mechanism_type": "mechanism_type=10",
    #     "atom1": "atom1.ring=3",
    #     "atom2": "atom2.ring=3",
    #     "atom3": "atom3.ring=3",
    #     "atom4": "atom4.ring=3",
    #     "bond1": "bond1=unused",
    #     "bond2": "bond2=unused",
    #     "new_bond_ring_size": "ring>=7",
    # }

    # for section in section_layout:
    #     name = str(section["section"])
    #     section_entries = entries_by_section[name]
    #     if str(section_entries[0]["label"]) != first_labels[name]:
    #         raise ValueError(
    #             f"First label mismatch for {name}: expected={first_labels[name]}, actual={section_entries[0]['label']}"
    #         )
    #     if str(section_entries[-1]["label"]) != last_labels[name]:
    #         raise ValueError(
    #             f"Last label mismatch for {name}: expected={last_labels[name]}, actual={section_entries[-1]['label']}"
    #         )


__all__ = [
    "ATOM_FEATURE_GROUPS",
    "BOND_FEATURE_LABELS",
    "MECHANISM_TYPE_LABELS",
    "RING_SIZE_FEATURE_LABELS",
    "atom_feature_size",
    "build_feature_entries",
    "build_feature_map",
    "build_section_layout",
    "build_schema",
    "export_schema_json",
    "fingerprint_size",
    "validate_schema_against_implementation",
]
