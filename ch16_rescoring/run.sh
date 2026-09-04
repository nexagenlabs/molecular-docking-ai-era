#!/usr/bin/env bash
# Chapter 16 - rescoring, and what an enrichment factor is worth.
#
#   bash ch16_rescoring/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi

$PYTHON ch16_rescoring/scripts/enrichment_arithmetic.py

echo
echo "=============================================================="
echo " The GNINA pipeline. It needs a GPU and a compiled binary."
echo "=============================================================="
# Expected to fail here with exit 3 and an explanation; the rest of the
# chapter does not depend on it.
bash ch16_rescoring/scripts/rescore_with_gnina.sh || true

echo
echo "Results:  ch16_rescoring/outputs/rescoring.md"
echo "Expected: ch16_rescoring/outputs/expected/results.md"
