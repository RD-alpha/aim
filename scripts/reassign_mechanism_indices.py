#!/usr/bin/env python3
"""
Reassign mechanisms where mechanism[0] is 6 or 7:
- Move mechanism[1] to mechanism[3]
- Set mechanism[1] to None
- Error if mechanism[3] is already not None
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(", ", ": "))


def _iter_data_json(root: str):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name == "data.json":
                yield os.path.join(dirpath, name)


def _validate_mechanism(mech: Any, path: str, choice_key: str) -> List[Any]:
    if not isinstance(mech, list):
        raise ValueError(f"{path}: choice {choice_key} mechanism is not a list: {type(mech).__name__}")
    if len(mech) < 4:
        raise ValueError(f"{path}: choice {choice_key} mechanism has length {len(mech)} (<4)")
    return mech


def process_file(path: str, dry_run: bool) -> int:
    data = _load_json(path)
    choices = data.get("choices")
    if choices is None:
        return 0
    if not isinstance(choices, dict):
        raise ValueError(f"{path}: 'choices' is not a dict: {type(choices).__name__}")

    changed = 0
    for choice_key, choice_val in choices.items():
        if not isinstance(choice_val, dict):
            raise ValueError(f"{path}: choice {choice_key} is not a dict: {type(choice_val).__name__}")
        mech = choice_val.get("mechanism")
        if mech is None:
            continue
        mech = _validate_mechanism(mech, path, str(choice_key))

        if mech[0] in (6, 7):
            if mech[3] is not None:
                raise ValueError(
                    f"{path}: choice {choice_key} mechanism[3] must be None but is {mech[3]!r}"
                )
            mech[3] = mech[1]
            mech[1] = None
            changed += 1

    if changed and not dry_run:
        _dump_json(path, data)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default="training_sets/20260202",
        help="Root folder to scan (default: training_sets/20260202)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Scan and report without writing files")
    args = parser.parse_args()

    total_changed = 0
    total_files = 0
    for path in _iter_data_json(args.root):
        try:
            total_files += 1
            total_changed += process_file(path, args.dry_run)
        except Exception as e:
            print(f"Error processing {path}: {e}")
            total_changed -=1

    print(f"Scanned {total_files} data.json files")
    print(f"Updated {total_changed} mechanisms")
    if args.dry_run:
        print("Dry run: no files were modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
