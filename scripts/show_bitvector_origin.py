#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D


def parse_origin_line(line: str) -> tuple[int, Path, str]:
    parts = [part.strip() for part in line.strip().split(",")]
    if len(parts) != 3:
        raise ValueError(f"Expected '<bitvector_idx>,<folder>,<choice_id>', got: {line!r}")
    bitvector_idx = int(parts[0])
    folder = Path(parts[1])
    choice_id = parts[2]
    return bitvector_idx, folder, choice_id


def load_origin_from_file(origins_path: Path, bitvector_idx: int) -> tuple[int, Path, str]:
    with origins_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx, folder, choice_id = parse_origin_line(line)
            if idx == bitvector_idx:
                return idx, folder, choice_id
    raise ValueError(f"Bitvector index {bitvector_idx} not found in {origins_path}")


def render_molecule(mol: Chem.Mol, out_path: Path) -> None:
    drawer = rdMolDraw2D.MolDraw2DCairo(700, 500)
    options = drawer.drawOptions()
    options.addAtomIndices = True
    options.bondLineWidth = 2
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    out_path.write_bytes(drawer.GetDrawingText())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show the molecule/mechanism corresponding to a bitvector origin."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--origin-line",
        help='Literal origin line, e.g. "515,training_sets/20260202/35,5"',
    )
    group.add_argument(
        "--bitvector-index",
        type=int,
        help="Bitvector index to look up inside bitvector_origins.txt",
    )
    parser.add_argument(
        "--origins-file",
        default="bitvector_origins.txt",
        help="Path to bitvector_origins.txt",
    )
    parser.add_argument(
        "--output",
        help="Optional output PNG path. Defaults to origin_<idx>_<choice>.png next to the data folder.",
    )
    args = parser.parse_args()

    if args.origin_line:
        bitvector_idx, folder, choice_id = parse_origin_line(args.origin_line)
    else:
        bitvector_idx, folder, choice_id = load_origin_from_file(
            Path(args.origins_file), args.bitvector_index
        )

    data_path = folder / "data.json"
    mol_path = folder / "sm.pkl"

    with data_path.open() as f:
        data = json.load(f)
    with mol_path.open("rb") as f:
        mol = pickle.load(f)

    choice = data["choices"][str(choice_id)]
    mechanism = choice["mechanism"]
    probable = choice.get("probable")
    smiles = Chem.MolToSmiles(mol)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = folder / f"origin_{bitvector_idx}_{choice_id}.png"

    render_molecule(mol, out_path)

    print(f"bitvector_index: {bitvector_idx}")
    print(f"folder: {folder}")
    print(f"choice_id: {choice_id}")
    print(f"smiles: {smiles}")
    print(f"mechanism: {mechanism}")
    print(f"probable: {probable}")
    print(f"image: {out_path}")


if __name__ == "__main__":
    main()
