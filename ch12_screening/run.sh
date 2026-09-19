#!/usr/bin/env bash
# Chapter 12 - the mechanics of a screen, and what it would cost.
#
#   bash ch12_screening/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message
if [ ! -f data/structures/1L2S.pdb ]; then bash data/structures/fetch.sh; fi
if [ ! -f data/ligands/STC.sdf ]; then $PYTHON data/ligands/generate.py; fi
$PYTHON ch12_screening/scripts/screen.py "$@"
echo
echo "Results:  ch12_screening/outputs/screen.md"
echo "Expected: ch12_screening/outputs/expected/results.md"
