#!/usr/bin/env bash
# Chapter 2 - choosing a method, from measurements rather than reputation.
#
#   bash ch02_method_choice/run.sh
#
# Reads the other chapters' output files. Any chapter that has not been run
# shows as "not measured" rather than as a default.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
$PYTHON ch02_method_choice/scripts/choose_method.py
echo
echo "Results:  ch02_method_choice/outputs/method_choice.md"
echo "Expected: ch02_method_choice/outputs/expected/results.md"
