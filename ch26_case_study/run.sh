#!/usr/bin/env bash
# Chapter 26 - three reproduction tests with published answers.
#
#   bash ch26_case_study/run.sh
#
# Nine docking runs at exhaustiveness 32; allow about five minutes.
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

$PYTHON ch26_case_study/scripts/case_study.py

echo
echo "Results:  ch26_case_study/outputs/case_study.md"
echo "Expected: ch26_case_study/outputs/expected/results.md"
