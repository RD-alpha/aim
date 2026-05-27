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


def validate_mechanism(mechanism: object) -> None:
    if not isinstance(mechanism, list) or len(mechanism) != 5:
        raise ValueError(f"Mechanism must be a 5-item list, got: {mechanism!r}")


def load_model(model_path: str) -> xgb.XGBClassifier:
    clf = xgb.XGBClassifier()
    clf.load_model(model_path)
    return clf


def format_value(value: float) -> str:
    if np.isnan(value):
        return "missing"
    if value == 1:
        return "on"
    if value == 0:
        return "off"
    return f"{value:.6g}"


def mechanism_atom_summary(mol: Chem.Mol, mechanism: list[int | None]) -> list[str]:
    rows = []
    for slot, atom_idx in enumerate(mechanism[1:], start=1):
        if atom_idx is None:
            rows.append(f"atom{slot}: None")
            continue

        atom = mol.GetAtomWithIdx(atom_idx)
        map_num = atom.GetAtomMapNum()
        mapped = f" map={map_num}" if map_num else ""
        rows.append(
            f"atom{slot}: idx={atom_idx}{mapped} "
            f"{atom.GetSymbol()} charge={atom.GetFormalCharge()} "
            f"H={atom.GetTotalNumHs()} hybrid={atom.GetHybridization()}"
        )
    return rows


def contribution_rows(
    fingerprint: np.ndarray, contributions: np.ndarray
) -> list[dict[str, object]]:
    feature_map = build_feature_map()
    rows = []
    for idx, contribution in enumerate(contributions[:-1]):
        if abs(float(contribution)) < 1e-12:
            continue
        rows.append(
            {
                "index": idx,
                "feature": feature_map.get(idx, f"f{idx}"),
                "value": format_value(float(fingerprint[idx])),
                "contribution": float(contribution),
            }
        )
    return rows


def print_table(title: str, rows: list[dict[str, object]], limit: int) -> None:
    shown = rows[:limit]
    print(title)
    print("-" * len(title))
    if not shown:
        print("(none)")
        print()
        return

    print(f"{'rank':>4}  {'idx':>4}  {'value':>8}  {'contrib':>10}  feature")
    for rank, row in enumerate(shown, start=1):
        print(
            f"{rank:>4}  {row['index']:>4}  {row['value']:>8}  "
            f"{row['contribution']:>+10.6f}  {row['feature']}"
        )
    print()


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

    fingerprint = np.array(make_fingerprint(mol, mechanism), dtype=float)
    x = fingerprint.reshape(1, -1)

    clf = load_model(args.model)
    expected_features = clf.get_booster().num_features()
    actual_features = x.shape[1]
    if actual_features != expected_features:
        raise ValueError(
            "Model/fingerprint feature mismatch: "
            f"model expects {expected_features} features, fingerprint has {actual_features}. "
            "Pick a compatible model or retrain the model on the current fingerprint layout."
        )

    probability = float(clf.predict_proba(x)[0, 1])
    prediction = int(clf.predict(x)[0])

    dmatrix = xgb.DMatrix(x)
    contributions = clf.get_booster().predict(dmatrix, pred_contribs=True)[0]
    base_value = float(contributions[-1])
    raw_score = float(np.sum(contributions))
    probability_from_contribs = 1.0 / (1.0 + math.exp(-raw_score))

    rows = contribution_rows(fingerprint, contributions)
    positive = sorted(
        [row for row in rows if float(row["contribution"]) > 0],
        key=lambda row: float(row["contribution"]),
        reverse=True,
    )
    negative = sorted(
        [row for row in rows if float(row["contribution"]) < 0],
        key=lambda row: float(row["contribution"]),
    )
    absolute = sorted(rows, key=lambda row: abs(float(row["contribution"])), reverse=True)

    print(f"model: {args.model}")
    print(f"prediction: {prediction}")
    print(f"probability_positive: {probability:.6f}")
    print(f"probability_from_contributions: {probability_from_contribs:.6f}")
    print(f"raw_score: {raw_score:.6f}")
    print(f"base_value: {base_value:.6f}")
    print(f"fingerprint_length: {actual_features}")
    print(f"mechanism: {mechanism}")
    print()

    if not args.hide_atoms:
        print("Mechanism atoms")
        print("---------------")
        for line in mechanism_atom_summary(mol, mechanism):
            print(line)
        print()

    print_table("Positive evidence for class 1", positive, args.top)
    print_table("Negative evidence against class 1", negative, args.top)
    print_table("Largest absolute contributions", absolute, args.top)


if __name__ == "__main__":
    main()
