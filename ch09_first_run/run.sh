#!/usr/bin/env bash
# Chapter 9 - your first docking run.
#
#   bash ch09_first_run/run.sh
#
# Start to finish: fetches the structure if it is missing, prepares the
# receptor and ligand, runs the four demonstrations, writes outputs/results.md.
set -euo pipefail

cd "$(dirname "$0")/.."

# Prefer the repository's virtual environment, so a reader who followed
# environment/README.md does not have to remember to activate it.
if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "python: $($PYTHON --version 2>&1)"

# Vina 1.2.7 exactly. 1.2.5 was superseded in February 2025 and none of the
# numbers in this repository were measured with it.
if [ -n "${VINA:-}" ]; then
  VINA_BIN="$VINA"
elif [ -x ".tools/vina.exe" ]; then
  VINA_BIN=".tools/vina.exe"
elif [ -x ".tools/vina" ]; then
  VINA_BIN=".tools/vina"
elif command -v vina >/dev/null 2>&1; then
  VINA_BIN="vina"
else
  echo "Vina not found. Set \$VINA or see environment/README.md." >&2
  exit 1
fi
echo "vina:   $("$VINA_BIN" --version | head -1)"

if [ ! -f data/structures/1L2S.pdb ]; then
  echo
  echo "1L2S.pdb not present; fetching."
  bash data/structures/fetch.sh
fi

if [ ! -f data/ligands/STC.sdf ]; then
  echo
  echo "STC.sdf not present; generating the reference copies."
  $PYTHON data/ligands/generate.py
fi

echo
echo "=============================================================="
echo " Preparing inputs"
echo "=============================================================="
$PYTHON ch09_first_run/prepare_inputs.py

echo
echo "=============================================================="
echo " Running the four demonstrations"
echo "=============================================================="
$PYTHON ch09_first_run/experiments.py "$@"

echo
echo "Results:  ch09_first_run/outputs/results.md"
echo "Expected: ch09_first_run/outputs/expected/results.md"
