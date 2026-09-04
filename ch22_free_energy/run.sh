#!/usr/bin/env bash
# Chapter 22 - can a free-energy calculation resolve this series?
#
#   bash ch22_free_energy/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi

$PYTHON ch22_free_energy/scripts/power.py
echo
echo "Results:  ch22_free_energy/outputs/"
echo "Expected: ch22_free_energy/outputs/expected/"
