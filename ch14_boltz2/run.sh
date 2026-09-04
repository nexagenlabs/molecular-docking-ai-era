#!/usr/bin/env bash
# Chapter 14 - Boltz-2 against FEP+, and the squaring step.
#
#   bash ch14_boltz2/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
$PYTHON ch14_boltz2/scripts/correlation.py
echo
echo "Results:  ch14_boltz2/outputs/correlation.md"
echo "Figure:   ch14_boltz2/outputs/correlation.png"
echo "Expected: ch14_boltz2/outputs/expected/results.md"
