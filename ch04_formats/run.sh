#!/usr/bin/env bash
# Chapter 4 - what each file format destroys.
#
#   bash ch04_formats/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

if [ ! -f data/ligands/STC.sdf ]; then
  echo "reference ligands not present; generating."
  $PYTHON data/ligands/generate.py
fi

$PYTHON ch04_formats/scripts/roundtrip.py

echo
echo "Results:  ch04_formats/outputs/roundtrip.md"
echo "Expected: ch04_formats/outputs/expected/results.md"
