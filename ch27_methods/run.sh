#!/usr/bin/env bash
# Chapter 27 - the methods section, generated from the record.
#
#   bash ch27_methods/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
if [ ! -f ch20_protocol_record/outputs/filled_record.json ]; then
  echo "protocol record not present; running ch20."
  bash ch20_protocol_record/run.sh
fi
$PYTHON ch27_methods/scripts/write_methods.py
echo
echo "Results:  ch27_methods/outputs/"
echo "Expected: ch27_methods/outputs/expected/"
