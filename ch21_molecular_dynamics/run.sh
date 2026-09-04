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

if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

$PYTHON ch21_molecular_dynamics/scripts/convergence.py

echo
echo "Results:  ch21_molecular_dynamics/outputs/convergence.md"
echo "Figure:   ch21_molecular_dynamics/outputs/convergence.png"
echo "Expected: ch21_molecular_dynamics/outputs/expected/results.md"
