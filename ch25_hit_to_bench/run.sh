#!/usr/bin/env bash
# Chapter 25 - from a docking hit to an experiment.
#
#   bash ch25_hit_to_bench/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi

$PYTHON ch25_hit_to_bench/scripts/design_assay.py
echo
echo "Results:  ch25_hit_to_bench/outputs/"
echo "Expected: ch25_hit_to_bench/outputs/expected/"
