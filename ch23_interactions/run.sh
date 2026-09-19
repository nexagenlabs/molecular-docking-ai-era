#!/usr/bin/env bash
# Chapter 23 - what the pose is actually touching.
#
#   bash ch23_interactions/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message

if [ ! -f ch17_validation/outputs/work/1L2S_pose.sdf ]; then
  echo "ch17 has not been run; running it to produce the poses."
  bash ch17_validation/run.sh
fi

$PYTHON ch23_interactions/scripts/fingerprint.py

echo
echo "Results:  ch23_interactions/outputs/fingerprint.md"
echo "Expected: ch23_interactions/outputs/expected/results.md"
