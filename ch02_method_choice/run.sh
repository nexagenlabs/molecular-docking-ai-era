#!/usr/bin/env bash
# Chapter 2 - choosing a method, from measurements rather than reputation.
#
#   bash ch02_method_choice/run.sh
#
# Reads the other chapters' output files. Any chapter that has not been run
# shows as "not measured" rather than as a default.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/run_common.sh   # sets PYTHON, or stops with one message
$PYTHON ch02_method_choice/scripts/choose_method.py
echo
echo "Results:  ch02_method_choice/outputs/method_choice.md"
echo "Expected: ch02_method_choice/outputs/expected/results.md"
