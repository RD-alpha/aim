#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${1:-/home/rd611/aim}"
DEST="${2:-ziggy:/home/rd611/aim}"

rsync -av --delete \
  "${SRC_DIR}/shared/" \
  "${DEST}/shared/"

rsync -av \
  "${SRC_DIR}/models/" \
  "${DEST}/models/"

rsync -av \
  "${SRC_DIR}/unique_positive_bitvectors.txt" \
  "${SRC_DIR}/unique_bitvectors.txt" \
  "${DEST}/"

echo "Sync complete: ${DEST}"
