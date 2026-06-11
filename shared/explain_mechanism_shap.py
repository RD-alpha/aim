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


from .fingerprint_schema import build_feature_map
from .ml_helper import make_fingerprint
import os


DEFAULT_MODEL = "models/v110/xg_model.json"




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


def explain(mol, mechanism, model_path, top=10) -> None:
   
    validate_mechanism(mechanism)
    fingerprint = np.array(make_fingerprint(mol, mechanism), dtype=float)
    x = fingerprint.reshape(1, -1)

    clf = load_model(model_path)
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

    print(f"model: {model_path}")
    print(f"prediction: {prediction}")
    print(f"probability_positive: {probability:.6f}")
    print(f"probability_from_contributions: {probability_from_contribs:.6f}")
    print(f"raw_score: {raw_score:.6f}")
    print(f"base_value: {base_value:.6f}")
    print(f"fingerprint_length: {actual_features}")
    print(f"mechanism: {mechanism}")
    print()


    print("Mechanism atoms")
    print("---------------")
    for line in mechanism_atom_summary(mol, mechanism):
        print(line)
    print()

    print_table("Positive evidence for class 1", positive, top)
    print_table("Negative evidence against class 1", negative, top)
    print_table("Largest absolute contributions", absolute, top)

def natural_language_explain(mol, mechanism, model_path, top=5) -> None:
    bond_types = {1: 'single', 2: 'double', 3: 'triple'}
    def source_text(atom1, atom3):
        if mechanism[0] in [0, 1, 4]:
            return f"The lone pair on {atom1} attacks "
        elif mechanism[0] in [2, 3, 5]:
            bond_order = int(mol.GetBondBetweenAtoms(mechanism[1], mechanism[3]).GetBondTypeAsDouble())
            return f"The electrons in the {bond_types[bond_order]} bond between {atom1} and {atom3} (bond 1), going through atom 1, attack "
        else:
            return ""
        
    def sink_text(atom2, atom4):
        if mechanism[0] in [0, 2, 6]:
            return f"the vacant orbital on {atom2}."
        elif mechanism[0] in [1, 3]:
            bond_order = int(mol.GetBondBetweenAtoms(mechanism[2], mechanism[4]).GetBondTypeAsDouble())
            return f"the {bond_types[bond_order]} bond between {atom2} and {atom4} (bond 2), forming a bond between atom 1 and atom 2."
        elif mechanism[0] == 7:
            bond_order = int(mol.GetBondBetweenAtoms(mechanism[2], mechanism[4]).GetBondTypeAsDouble())   
            return f"the {bond_types[bond_order]} bond between {atom2} and {atom4} (bond 2), forming a bond between H and atom 2."
        else:
            return ""  
    
    def proton_text(atom):
        if mechanism[0] in [4, 5]:
            return f"the proton on {atom}, deprotonating it."
        else:
            return ""

    def hydride_text(atom):
        if mechanism[0] in [6, 7]:
            return f"The hydridic H on {atom}, attacks "
        else:
            return ""
        
    def elimination_text(atom1, atom2, atom3, atom4):
        if mechanism [0] == 8:
            return f"The lone pair on {atom1} removes a proton from {atom3}, and a bond forms between atom 3 and {atom2}."
        elif mechanism[0] == 9:
            bond_order = int(mol.GetBondBetweenAtoms(mechanism[2], mechanism[4]).GetBondTypeAsDouble())
            return f"The lone pair on {atom1} removes a proton from {atom3}, and a bond forms between atom 3 and {atom2}, breaking the {bond_types[bond_order]}bond between atom 2 and {atom4} (bond 2)."
        else:
            return ""
        
    def bond_break_text(atom2, atom4):
        if mechanism[0] == 10:
            bond_order = int(mol.GetBondBetweenAtoms(mechanism[2], mechanism[4]).GetBondTypeAsDouble())
            return f"The {bond_types[bond_order]} bond between {atom2} and {atom4} (bond 2) breaks, with the electrons going to {atom4}."
        else:
            return ""

    atoms = []
    for slot, atom_idx in enumerate(mechanism[1:], start=1):
        if atom_idx is None:
            atoms.append(None)
            continue
        atom = mol.GetAtomWithIdx(atom_idx)
        atoms.append(f"atom {slot} ({atom.GetSymbol()})")

    parts = [
        source_text(atoms[0], atoms[2]),
        hydride_text(atoms[2]),
        proton_text(atoms[3]),
        sink_text(atoms[1], atoms[3]),
        elimination_text(
            atoms[0], atoms[1], atoms[2], atoms[3]
        ),
        bond_break_text(atoms[1], atoms[3]),
    ]
    text_description = "".join(part for part in parts if part).strip()

    validate_mechanism(mechanism)
    fingerprint = np.array(make_fingerprint(mol, mechanism), dtype=float)
    x = fingerprint.reshape(1, -1)

    clf = load_model(model_path)


    probability = float(clf.predict_proba(x)[0, 1])
    prediction = int(clf.predict(x)[0])

    dmatrix = xgb.DMatrix(x)
    contributions = clf.get_booster().predict(dmatrix, pred_contribs=True)[0]

    rows = contribution_rows(fingerprint, contributions)
    absolute = sorted(rows, key=lambda row: abs(float(row["contribution"])), reverse=True)
    prediction_text = f"Prediction: {prediction} (probability_positive: {probability:.6f})\n"

    shown = absolute[:top]
    shap_table = (f"{'rank':>4}  {'value':>8}  {'contribution':>10}  feature")
    for rank, row in enumerate(shown, start=1):
            shap_table += f"\n{rank:>4} {row['value']:>8} {row['contribution']:>+10.2f}  {row['feature']}"

    prompt_text = f"You are given the following curly arrow mechanism and the results of a prediction model that predicts whether or not it is feasible. It lists the contributions from the features in order of their importance. Explain using the results of the model why the mechanism is predicted to be feasible or not.\n"
    return prompt_text + text_description + "\n\n" + prediction_text + "\n" + shap_table


