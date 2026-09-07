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
# The exit code is propagated, not swallowed. `|| true` used to sit here, so
# the chapter exited 0 while its own script exited 3 saying it could not run --
# the prose was honest and the exit code was not, and a machine reading exit
# codes could not tell a full run from a skipped one. That is the same defect
# as ch20's silent missing log, one file along.
#
# The footer still prints either way: a reader who cannot run the prediction
# should still be told where the input file they *can* check has been written.
set +e
$PYTHON ch13_cofolding/scripts/cofold.py
status=$?
set -e

echo
echo "Input:    ch13_cofolding/outputs/ampc_stc.yaml"
echo "Results:  ch13_cofolding/outputs/cofolding.md"
if [ "$status" -ne 0 ]; then
  echo
  echo "Chapter 13 exits $status: the prediction did not run here. The input"
  echo "file above was still written and is the half that can be checked"
  echo "without a GPU."
fi
exit $status
