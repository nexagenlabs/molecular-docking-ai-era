#!/usr/bin/env bash
# Chapter 5 - receptor quality control, before anything is docked.
#
#   bash ch05_receptor_prep/run.sh [PDBID ...]
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

if [ ! -f data/structures/1L2S.pdb ]; then
  echo "structures not present; fetching."
  bash data/structures/fetch.sh
fi

$PYTHON ch05_receptor_prep/scripts/qc_report.py "$@"

echo
echo "Reports:  ch05_receptor_prep/outputs/qc_<PDBID>.md"
echo "Expected: ch05_receptor_prep/outputs/expected/"
