#!/usr/bin/env bash
# Chapter 8 - ligand preparation: protonation, stereochemistry, conformers.
#
#   bash ch08_ligand_prep/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message

$PYTHON ch08_ligand_prep/scripts/prepare_ligands.py

echo
echo "Results:  ch08_ligand_prep/outputs/ligand_prep.md"
echo "Expected: ch08_ligand_prep/outputs/expected/results.md"
