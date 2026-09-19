#!/usr/bin/env bash
# Chapter 27 - the methods section, generated from the record.
#
#   bash ch27_methods/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message
if [ ! -f ch20_protocol_record/outputs/filled_record.json ]; then
  echo "protocol record not present; running ch20."
  bash ch20_protocol_record/run.sh
fi
$PYTHON ch27_methods/scripts/write_methods.py
echo
echo "Results:  ch27_methods/outputs/"
echo "Expected: ch27_methods/outputs/expected/"
