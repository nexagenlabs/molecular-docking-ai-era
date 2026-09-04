#!/usr/bin/env bash
# Chapter 7 - where is the pocket, and what does getting it wrong cost?
#
#   bash ch07_pocket/run.sh
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

$PYTHON ch07_pocket/scripts/define_pocket.py

echo
echo "Results:  ch07_pocket/outputs/pocket.md"
echo "Expected: ch07_pocket/outputs/expected/results.md"
