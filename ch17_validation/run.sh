#!/usr/bin/env bash
# Chapter 17 - does the protocol reproduce the crystallographic pose?
#
#   bash ch17_validation/run.sh [PDBID ...]
#
# Takes about three minutes: three redocks at exhaustiveness 32, plus a
# sensitivity check on the 4JXV chain choice.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

if [ ! -f data/structures/1L2S.pdb ]; then
  echo "structures not present; fetching."
  bash data/structures/fetch.sh
fi
if [ ! -f data/ligands/STC.sdf ]; then
  echo "reference ligands not present; generating."
  $PYTHON data/ligands/generate.py
fi

$PYTHON ch17_validation/scripts/validate.py "$@"

echo
echo "Record:   ch17_validation/outputs/validation_record.md"
echo "Expected: ch17_validation/outputs/expected/results.md"
