#!/usr/bin/env bash
# Chapter 8 - ligand preparation: protonation, stereochemistry, conformers.
#
#   bash ch08_ligand_prep/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

$PYTHON ch08_ligand_prep/scripts/prepare_ligands.py

echo
echo "Results:  ch08_ligand_prep/outputs/ligand_prep.md"
echo "Expected: ch08_ligand_prep/outputs/expected/results.md"
