#!/usr/bin/env python3
from __future__ import annotations

import argparse

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.fingerprint_schema import export_schema_json, validate_schema_against_implementation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the fingerprint layout and export a JSON schema."
    )
    parser.add_argument(
        "--output",
        default="shared/fingerprint_schema.json",
        help="Path to write the exported schema JSON.",
    )
    args = parser.parse_args()

    validate_schema_against_implementation()
    output_path = export_schema_json(args.output)
    print(f"Wrote fingerprint schema to {output_path}")


if __name__ == "__main__":
    main()
