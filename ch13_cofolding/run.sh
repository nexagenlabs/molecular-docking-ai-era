#!/usr/bin/env bash
# Chapter 13 - co-folding.
#
#   bash ch13_cofolding/run.sh
#
# Writes the Boltz-2 input, then attempts the prediction. On a machine without
# a GPU the attempt exits 3 with an explanation; the input file is the half a
# reader can check either way.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
$PYTHON ch13_cofolding/scripts/cofold.py || true
echo
echo "Input:    ch13_cofolding/outputs/ampc_stc.yaml"
echo "Results:  ch13_cofolding/outputs/cofolding.md"
