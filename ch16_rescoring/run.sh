#!/usr/bin/env bash
# Chapter 16 - rescoring, and what an enrichment factor is worth.
#
#   bash ch16_rescoring/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message

$PYTHON ch16_rescoring/scripts/enrichment_arithmetic.py

echo
echo "=============================================================="
echo " The GNINA pipeline. It needs a GPU and a compiled binary."
echo "=============================================================="
# Expected to fail here with exit 3 and an explanation; the rest of the chapter
# does not depend on it. The exit code is propagated rather than swallowed:
# `|| true` used to sit here, so the chapter exited 0 while the pipeline exited
# 3 saying it could not run. The arithmetic above is published numbers and the
# rescoring is a thing that did not happen, and an exit code of 0 for both puts
# them on the same footing.
set +e
bash ch16_rescoring/scripts/rescore_with_gnina.sh
status=$?
set -e

echo
echo "Results:  ch16_rescoring/outputs/rescoring.md"
echo "Expected: ch16_rescoring/outputs/expected/results.md"
if [ "$status" -ne 0 ]; then
  echo
  echo "Chapter 16 exits $status: the arithmetic above ran, the GNINA"
  echo "rescoring did not. Both are in the results file, marked."
fi
exit $status
