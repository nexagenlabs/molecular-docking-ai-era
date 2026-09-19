#!/usr/bin/env bash
# Chapter 24 - enrichment analysis that refuses to run without a background.
#
#   bash ch24_network_pharmacology/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

echo "=============================================================="
echo " First, without a background. This is supposed to fail."
echo "=============================================================="
if $PYTHON ch24_network_pharmacology/scripts/enrichment.py; then
  echo "ERROR: the script ran without a background. That is the one thing" >&2
  echo "this chapter exists to prevent." >&2
  exit 1
fi
echo
echo "(exit code 2, as intended)"

echo
echo "=============================================================="
echo " Now with all three, side by side."
echo "=============================================================="
$PYTHON ch24_network_pharmacology/scripts/enrichment.py --compare

echo
echo "Results:  ch24_network_pharmacology/outputs/enrichment.md"
echo "Expected: ch24_network_pharmacology/outputs/expected/results.md"
