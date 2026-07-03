#!/usr/bin/env python3
"""Delete finetuning molecule pickles whose labels are still unset.

Each finetuning subfolder is expected to contain:

- data.json with choices keyed by molecule index
- mol_<index>.pkl files for generated candidate molecules

By default this script only prints what it would delete. Pass --apply to remove
the files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def iter_unlabeled_pickles(root: Path):
    for data_path in sorted(root.glob("*/data.json")):
        folder = data_path.parent
        try:
            data = json.loads(data_path.read_text())
        except json.JSONDecodeError as exc:
            yield folder, None, None, f"invalid JSON: {exc}"
            continue

        choices = data.get("choices", {})
        if not isinstance(choices, dict):
            yield folder, None, None, "missing or invalid choices object"
            continue

        for choice_id, info in sorted(choices.items(), key=lambda item: int(item[0]) if str(item[0]).isdigit() else str(item[0])):
            if not isinstance(info, dict):
                continue
            if info.get("probable") is None:
                yield folder, choice_id, folder / f"mol_{choice_id}.pkl", None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete mol_<id>.pkl files for finetuning choices with probable=null."
    )
    parser.add_argument(
        "--root",
        default="finetuning",
        type=Path,
        help="Root finetuning directory to scan. Default: finetuning",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files. Without this flag, only print a dry-run report.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary.",
    )
    args = parser.parse_args()

    root = args.root
    if not root.is_dir():
        raise SystemExit(f"Finetuning root does not exist or is not a directory: {root}")

    matched = 0
    deleted = 0
    missing = 0
    errors = 0

    for folder, choice_id, pkl_path, error in iter_unlabeled_pickles(root):
        if error is not None:
            errors += 1
            if not args.quiet:
                print(f"ERROR {folder}: {error}")
            continue

        matched += 1
        if not pkl_path.exists():
            missing += 1
            if not args.quiet:
                print(f"MISSING {pkl_path}")
            continue

        if args.apply:
            pkl_path.unlink()
            deleted += 1
            action = "DELETED"
        else:
            action = "WOULD DELETE"

        if not args.quiet:
            print(f"{action} {pkl_path}")

    mode = "apply" if args.apply else "dry-run"
    print(
        f"{mode}: matched {matched} unlabeled choices, "
        f"deleted {deleted}, missing {missing}, errors {errors}"
    )
    if not args.apply:
        print("Run again with --apply to delete the listed files.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
