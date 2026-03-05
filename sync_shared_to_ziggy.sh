#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${1:-/home/rd611/aim}"
DEST="${2:-ziggy:/home/rd611/aim}"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT
export TMP_DIR

rsync -av --delete \
  "${SRC_DIR}/shared/" \
  "${TMP_DIR}/shared/"

python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["TMP_DIR"]) / "shared" / "rules.py"
text = path.read_text()
needle = "def prepare_molecule("
if needle not in text:
    raise SystemExit("prepare_molecule not found in rules.py")

lines = text.splitlines()
out = []
in_prepare = False
already_has = False
inserted = False

for i, line in enumerate(lines):
    if line.startswith("def prepare_molecule("):
        in_prepare = True
    elif in_prepare and line.startswith("def "):
        in_prepare = False

    if in_prepare and "SetNoImplicit(False)" in line:
        already_has = True

for i, line in enumerate(lines):
    out.append(line)
    if line.startswith("def prepare_molecule(") and not already_has:
        indent = " " * 4
        out.append(f"{indent}for a in mol.GetAtoms():")
        out.append(f"{indent}    a.SetNoImplicit(False)")
        inserted = True

if inserted:
    path.write_text("\n".join(out) + "\n")
PY

python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["TMP_DIR"]) / "shared" / "next_step.py"
text = path.read_text()
needle = "def follow_on("
if needle not in text:
    raise SystemExit("follow_on not found in next_step.py")

lines = text.splitlines()
out = []
in_follow_on = False
already_has_fp_list = False
inserted_fp_list = False
inserted_append = False
updated_return = False

for line in lines:
    if line.startswith("def follow_on("):
        in_follow_on = True
    elif in_follow_on and line.startswith("def "):
        in_follow_on = False

    if in_follow_on and "fp_list = []" in line:
        already_has_fp_list = True

for line in lines:
    out.append(line)
    if line.startswith("def follow_on(") and not already_has_fp_list:
        indent = " " * 4
        out.append(f"{indent}fp_list = []")
        inserted_fp_list = True

for i, line in enumerate(out):
    if "smiles_list.append" in line and "fp_list.append" not in out[i+1:i+3]:
        indent = line[:len(line) - len(line.lstrip())]
        out.insert(i + 1, f"{indent}fp_list.append(fp)")
        inserted_append = True
        break

for i, line in enumerate(out):
    if line.strip() == "return (accepted_follow_on, smiles_list)":
        out[i] = "    return (accepted_follow_on, smiles_list, fp_list)"
        updated_return = True
        break

if inserted_fp_list or inserted_append or updated_return:
    path.write_text("\n".join(out) + "\n")
PY

rsync -av --delete \
  "${TMP_DIR}/shared/" \
  "${DEST}/shared/"

rsync -av \
  "${SRC_DIR}/models/" \
  "${DEST}/models/"

rsync -av \
  "${SRC_DIR}/unique_positive_bitvectors.txt" \
  "${SRC_DIR}/unique_bitvectors.txt" \
  "${DEST}/"

echo "Sync complete: ${DEST}"
