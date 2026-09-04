#!/usr/bin/env bash
# Chapter 3 - databases, cross-checked against themselves.
#
#   bash ch03_databases/run.sh
#
# Needs network access for the RCSB REST API.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi

if [ ! -f data/structures/1L2S.pdb ]; then
  echo "structures not present; fetching."
  bash data/structures/fetch.sh
fi
if [ ! -f data/ligands/STC.sdf ]; then
  $PYTHON data/ligands/generate.py
fi

$PYTHON ch03_databases/scripts/cross_check.py

echo
echo "Results:  ch03_databases/outputs/cross_check.md"
echo "Expected: ch03_databases/outputs/expected/results.md"
