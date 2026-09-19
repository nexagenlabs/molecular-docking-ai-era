#!/usr/bin/env bash
# Chapter 22 - can a free-energy calculation resolve this series?
#
#   bash ch22_free_energy/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message

$PYTHON ch22_free_energy/scripts/power.py
echo
echo "Results:  ch22_free_energy/outputs/"
echo "Expected: ch22_free_energy/outputs/expected/"
