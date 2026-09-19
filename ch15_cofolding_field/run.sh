#!/usr/bin/env bash
# Chapter 15 - the co-folding field.
#
#   bash ch15_cofolding_field/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message
if [ ! -f data/structures/1L2S.pdb ]; then bash data/structures/fetch.sh; fi
if [ ! -f data/ligands/STC.sdf ]; then $PYTHON data/ligands/generate.py; fi
$PYTHON ch15_cofolding_field/scripts/compare_methods.py
echo
echo "Results:  ch15_cofolding_field/outputs/"
echo "Expected: ch15_cofolding_field/outputs/expected/"
