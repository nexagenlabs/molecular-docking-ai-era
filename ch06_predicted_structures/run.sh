#!/usr/bin/env bash
# Chapter 6 - can you dock into a predicted structure?
#
#   bash ch06_predicted_structures/run.sh
#
# Fetches the AlphaFold model of AmpC and needs network access the first time.
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

if [ ! -f data/structures/1L2S.pdb ]; then
  echo "structures not present; fetching."
  bash data/structures/fetch.sh
fi
if [ ! -f data/ligands/STC.sdf ]; then
  echo "reference ligands not present; generating."
  $PYTHON data/ligands/generate.py
fi

$PYTHON ch06_predicted_structures/scripts/compare_alphafold.py

echo
echo "Results:  ch06_predicted_structures/outputs/alphafold_comparison.md"
echo "Expected: ch06_predicted_structures/outputs/expected/results.md"
