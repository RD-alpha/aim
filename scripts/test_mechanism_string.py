#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import numpy as np
import xgboost as xgb
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.ml_helper import make_fingerprint


DEFAULT_MODEL = "models/v109/xg_model.json"


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
                "Input must contain either a 'Mol ...' / 'Mechanism: ...' block or two non-empty lines: SMILES then mechanism list."
            )
        smiles = lines[0]
        mechanism = ast.literal_eval(lines[1])

    if not isinstance(mechanism, list) or len(mechanism) != 5:
        raise ValueError(f"Mechanism must be a 5-item list, got: {mechanism!r}")

    return smiles, mechanism


def load_model(model_path: str) -> xgb.XGBClassifier:
    clf = xgb.XGBClassifier()
    clf.load_model(model_path)
    return clf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a pasted Mol/Mechanism block, build the fingerprint, and score it with the model."
    )
    parser.add_argument(
        "input_text",
        help="Either a pasted block/string containing both the molecule and mechanism, or the SMILES string when used with mechanism_text.",
    )
    parser.add_argument(
        "mechanism_text",
        nargs="?",
        help="Optional mechanism list like '[1, 17, 0, None, 9]'. If omitted, input_text is parsed as a combined block.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Path to the model JSON. Defaults to {DEFAULT_MODEL}.",
    )
    args = parser.parse_args()

    if args.mechanism_text is not None:
        smiles = args.input_text.strip()
        mechanism = ast.literal_eval(args.mechanism_text.strip())
        if not isinstance(mechanism, list) or len(mechanism) != 5:
            raise ValueError(f"Mechanism must be a 5-item list, got: {mechanism!r}")
    else:
        smiles, mechanism = parse_input_block(args.input_text)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit could not parse the SMILES: {smiles}")

    fingerprint = make_fingerprint(mol, mechanism)
    x = np.array(fingerprint, dtype=float).reshape(1, -1)

    clf = load_model(args.model)
    expected_features = clf.get_booster().num_features()
    actual_features = x.shape[1]
    if actual_features != expected_features:
        raise ValueError(
            "Model/fingerprint feature mismatch: "
            f"model expects {expected_features} features, fingerprint has {actual_features}. "
            "Pick a compatible model or retrain the model on the current fingerprint layout."
        )

    pred = int(clf.predict(x)[0])

    prob_positive = None
    if hasattr(clf, "predict_proba"):
        try:
            prob_positive = float(clf.predict_proba(x)[0, 1])
        except Exception:
            prob_positive = None

    print(f"model: {args.model}")
    print(f"smiles: {smiles}")
    print(f"mechanism: {mechanism}")
    print(f"fingerprint_length: {len(fingerprint)}")
    print(f"prediction: {pred}")
    if prob_positive is not None:
        print(f"probability_positive: {prob_positive:.6f}")
    print("fingerprint:")
    print(fingerprint)


if __name__ == "__main__":
    main()
