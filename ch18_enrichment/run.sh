#!/usr/bin/env bash
# Chapter 18 - two screens with the same AUC and opposite usefulness.
#
#   bash ch18_enrichment/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

$PYTHON ch18_enrichment/scripts/enrichment.py

echo
echo "Results:  ch18_enrichment/outputs/metrics.md"
echo "Figure:   ch18_enrichment/outputs/enrichment.png"
echo "Expected: ch18_enrichment/outputs/expected/results.md"
