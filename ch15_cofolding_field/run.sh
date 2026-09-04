#!/usr/bin/env bash
# Chapter 15 - the co-folding field.
#
#   bash ch15_cofolding_field/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
if [ ! -f data/structures/1L2S.pdb ]; then bash data/structures/fetch.sh; fi
if [ ! -f data/ligands/STC.sdf ]; then $PYTHON data/ligands/generate.py; fi
$PYTHON ch15_cofolding_field/scripts/compare_methods.py
echo
echo "Results:  ch15_cofolding_field/outputs/"
echo "Expected: ch15_cofolding_field/outputs/expected/"
