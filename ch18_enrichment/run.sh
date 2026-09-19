#!/usr/bin/env bash
# Chapter 18 - two screens with the same AUC and opposite usefulness.
#
#   bash ch18_enrichment/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

# The construction first: it prints the book's four metrics for both
# screens and asserts the search lands on the recorded (hi, lo).
$PYTHON ch18_enrichment/scripts/ch18_make_screens.py
echo

# Then the measurement, report and figure, over the same screens.
$PYTHON ch18_enrichment/scripts/enrichment.py

echo
echo "Results:  ch18_enrichment/outputs/metrics.md"
echo "Figure:   ch18_enrichment/outputs/enrichment.png"
echo "Expected: ch18_enrichment/outputs/expected/results.md"
