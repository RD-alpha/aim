#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import math
import re
import sys
from pathlib import Path

import numpy as np
import xgboost as xgb
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.fingerprint_schema import build_feature_map
from shared.ml_helper import make_fingerprint
from shared.explain_mechanism_shap import validate_mechanism, explain


DEFAULT_MODEL = "models/v110/xg_model.json"


def parse_input_block(text: str) -> tuple[str, list[int | None]]:
    mol_match = re.search(r"Mol\s+\d+\s*-\s*(.+)", text)
    mech_match = re.search(r"Mechanism:\s*(\[[^\n\r]+\])", text)

    if mol_match and mech_match:
        smiles = mol_match.group(1).strip()
        mechanism = ast.literal_eval(mech_match.group(1).strip())
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            raise ValueError(
                "Input must contain either a 'Mol ...' / 'Mechanism: ...' block "
                "or two non-empty lines: SMILES then mechanism list."
            )
        smiles = lines[0]
        mechanism = ast.literal_eval(lines[1])

    validate_mechanism(mechanism)
    return smiles, mechanism


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pretty-print XGBoost SHAP-style feature contributions for a SMILES/mechanism pair."
    )
    parser.add_argument(
        "input_text",
        help="Either a pasted block/string containing both molecule and mechanism, or the SMILES string when used with mechanism_text.",
    )
    parser.add_argument(
        "mechanism_text",
        nargs="?",
        help="Optional mechanism list like '[1, 17, 0, None, 9]'. If omitted, input_text is parsed as a combined block.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Path to model JSON. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of positive and negative contributions to show.",
    )
    parser.add_argument(
        "--hide-atoms",
        action="store_true",
        help="Do not print mechanism atom slot details.",
    )
    args = parser.parse_args()

    if args.mechanism_text is not None:
        smiles = args.input_text.strip()
        mechanism = ast.literal_eval(args.mechanism_text.strip())
        validate_mechanism(mechanism)
    else:
        smiles, mechanism = parse_input_block(args.input_text)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit could not parse the SMILES: {smiles}")

    explain(mol, mechanism, args.model, args.top)


if __name__ == "__main__":
    main()
