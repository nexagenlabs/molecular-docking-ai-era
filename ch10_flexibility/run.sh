#!/usr/bin/env bash
# Chapter 10 - which binding-site side chains actually move.
#
#   bash ch10_flexibility/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

if [ ! -f data/structures/1L2S.pdb ]; then
  echo "structures not present; fetching."
  bash data/structures/fetch.sh
fi

$PYTHON ch10_flexibility/scripts/torsion_analysis.py

echo
echo "Results:  ch10_flexibility/outputs/rotamers.md"
echo "Expected: ch10_flexibility/outputs/expected/results.md"
