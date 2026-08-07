#!/usr/bin/env python3
"""Label a reaction fingerprint with the schema in shared/fingerprint_schema.py."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.fingerprint_schema import build_feature_entries, build_section_layout, fingerprint_size


def parse_scalar(value: str) -> float:
    value = value.strip()
    if value.lower() in {"nan", "none", "null", ""}:
        return math.nan
    return float(value)


def parse_fingerprint_text(text: str) -> list[float]:
    text = text.strip()
    if not text:
        raise ValueError("No fingerprint text was provided")

    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        parsed = None

    if isinstance(parsed, (list, tuple)):
        return [parse_scalar(str(value)) for value in parsed]

    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()

    if "\n" in text and "," in text:
        rows = list(csv.reader(line for line in text.splitlines() if line.strip()))
        if len(rows) != 1:
            raise ValueError(
                "Expected one fingerprint row. Use --row-index when reading a multi-row file."
            )
        return [parse_scalar(value) for value in rows[0]]

    parts = [part for part in re.split(r"[\s,]+", text) if part]
    return [parse_scalar(part) for part in parts]


def read_fingerprint(args: argparse.Namespace) -> list[float]:
    if args.file:
        with Path(args.file).open(newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            raise ValueError(f"No rows found in {args.file}")
        row_index = args.row_index
        if row_index < 0 or row_index >= len(rows):
            raise ValueError(f"--row-index {row_index} is outside the file range 0..{len(rows) - 1}")
        return [parse_scalar(value) for value in rows[row_index]]

    if args.fingerprint == "-":
        return parse_fingerprint_text(sys.stdin.read())

    return parse_fingerprint_text(args.fingerprint)


def normalize_fingerprint(values: list[float], *, allow_label: bool) -> tuple[list[float], float | None]:
    expected = fingerprint_size()
    label = None

    if len(values) == expected:
        return values, label

    if allow_label and len(values) == expected + 1:
        label = values[-1]
        return values[:-1], label

    raise ValueError(
        f"Fingerprint has {len(values)} values, but schema expects {expected}. "
        f"Pass --allow-label to accept a trailing label column ({expected + 1} values)."
    )


def is_nan(value: float) -> bool:
    return isinstance(value, float) and math.isnan(value)


def format_value(value: float) -> str:
    if is_nan(value):
        return "nan"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def labelled_rows(fingerprint: list[float]) -> list[dict[str, Any]]:
    entries = build_feature_entries()
    rows = []
    for entry, value in zip(entries, fingerprint):
        rows.append(
            {
                "index": entry["index"],
                "section": entry["section"],
                "group": entry["group"],
                "slot": entry["slot"],
                "label": entry["label"],
                "value": None if is_nan(value) else value,
                "display_value": format_value(value),
                "active": (not is_nan(value)) and value != 0,
                "missing": is_nan(value),
            }
        )
    return rows


def print_human(rows: list[dict[str, Any]], *, show_all: bool, show_missing: bool, label: float | None) -> None:
    active_count = sum(1 for row in rows if row["active"])
    missing_count = sum(1 for row in rows if row["missing"])
    print(f"fingerprint_length: {len(rows)}")
    if label is not None:
        print(f"trailing_label: {format_value(label)}")
    print(f"active_bits: {active_count}")
    print(f"missing_bits: {missing_count}")

    rows_by_section: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_section.setdefault(str(row["section"]), []).append(row)

    for section in build_section_layout():
        section_name = str(section["section"])
        section_rows = rows_by_section.get(section_name, [])
        printable = [
            row for row in section_rows if show_all or row["active"] or (show_missing and row["missing"])
        ]
        if not printable:
            continue

        print()
        print(f"{section_name} [{section['start']}-{section['end']}]:")
        for row in printable:
            marker = "*" if row["active"] else "-" if row["missing"] else " "
            print(
                f"  {marker} {int(row['index']):>3} "
                f"{row['label']:<36} value={row['display_value']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn a numeric fingerprint into human-readable feature labels."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "fingerprint",
        nargs="?",
        help="Fingerprint as a Python list, comma-separated string, whitespace-separated string, or '-' for stdin.",
    )
    input_group.add_argument(
        "--file",
        help="CSV file containing fingerprint rows.",
    )
    parser.add_argument(
        "--row-index",
        type=int,
        default=0,
        help="Zero-based row to read when using --file. Default: 0.",
    )
    parser.add_argument(
        "--allow-label",
        action="store_true",
        help="Accept and report a trailing label column, useful for bitvectors.csv rows.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print every schema bit, not just active bits.",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="Include missing/nan bits in the human-readable output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of grouped text.",
    )
    args = parser.parse_args()

    try:
        values = read_fingerprint(args)
        fingerprint, label = normalize_fingerprint(values, allow_label=args.allow_label)
    except ValueError as exc:
        parser.error(str(exc))

    rows = labelled_rows(fingerprint)

    if args.json:
        print(
            json.dumps(
                {
                    "fingerprint_length": len(fingerprint),
                    "trailing_label": None if label is None or is_nan(label) else label,
                    "active_bits": [row for row in rows if row["active"]],
                    "missing_bits": [row for row in rows if row["missing"]],
                    "rows": rows if args.all else None,
                },
                indent=2,
            )
        )
    else:
        print_human(rows, show_all=args.all, show_missing=args.missing, label=label)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
