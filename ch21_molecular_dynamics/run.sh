#!/usr/bin/env bash
# Chapter 21 - every window looks converged.
#
#   bash ch21_molecular_dynamics/run.sh
#
# No MD software needed: the trajectory is generated, not simulated. The
# GROMACS pipeline is a separate matter; this is about how trajectories are
# read, and a synthetic one lets the true answer be known.
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

# The construction first: it prints the book's window table and asserts
# each mean against it.
$PYTHON ch21_molecular_dynamics/scripts/ch21_make_trajectory.py
echo

# Then the analysis, report and figure, over the same trajectory.
$PYTHON ch21_molecular_dynamics/scripts/convergence.py

echo
echo "Results:  ch21_molecular_dynamics/outputs/convergence.md"
echo "Figure:   ch21_molecular_dynamics/outputs/convergence.png"
echo "Expected: ch21_molecular_dynamics/outputs/expected/results.md"
