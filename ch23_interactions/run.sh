#!/usr/bin/env bash
# Chapter 23 - what the pose is actually touching.
#
#   bash ch23_interactions/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi

if [ ! -f ch17_validation/outputs/work/1L2S_pose.sdf ]; then
  echo "ch17 has not been run; running it to produce the poses."
  bash ch17_validation/run.sh
fi

$PYTHON ch23_interactions/scripts/fingerprint.py

echo
echo "Results:  ch23_interactions/outputs/fingerprint.md"
echo "Expected: ch23_interactions/outputs/expected/results.md"
