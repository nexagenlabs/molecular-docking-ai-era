#!/usr/bin/env bash
# Chapter 9 - your first docking run.
#
#   bash ch09_first_run/run.sh
#
# Two systems, in this order and kept apart on purpose:
#
#   PART 1  a synthetic system - a ten-heavy-atom ligand in a shell of carbon
#           atoms. The book's timing and box-size numbers are these. They are
#           cheap and anyone can repeat them in seconds.
#
#   PART 2  AmpC - 1L2S chain B and STC. What a reader actually docks. It has
#           no published expected score, and its timings are nothing like the
#           synthetic ones.
#
# Conflating the two is how a reader ends up expecting 14 seconds on a real
# protein.
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/run_common.sh   # sets PYTHON, or stops with one message
echo "python: $($PYTHON --version 2>&1)"

# Vina 1.2.7 exactly. 1.2.5 was superseded in February 2025 and nothing in this
# repository was measured with it.
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

banner () {
  echo
  echo "=============================================================="
  echo " $1"
  echo "=============================================================="
}

# ---------------------------------------------------------------------------
# PART 1 - the synthetic system. These are the book's numbers.
# ---------------------------------------------------------------------------

banner "PART 1.0  Building the synthetic system"
$PYTHON ch09_first_run/scripts/make_test_system.py

banner "PART 1.1  The seed: Vina's default is random"
$PYTHON ch09_first_run/scripts/verify_run.py --system synthetic

banner "PART 1.2  Exhaustiveness: what 8 against 32 costs"
$PYTHON ch09_first_run/scripts/timing.py --system synthetic

banner "PART 1.3  Box size: an undersized box fails silently"
$PYTHON ch09_first_run/scripts/box_sweep.py --system synthetic

banner "PART 1.4  Mode 1's RMSD is not a validation result"
$PYTHON ch09_first_run/scripts/modes.py --system synthetic

# ---------------------------------------------------------------------------
# PART 2 - AmpC. No published expected score; this is the real system.
# ---------------------------------------------------------------------------

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

banner "PART 2.0  Preparing AmpC: 1L2S chain B and STC"
$PYTHON ch09_first_run/scripts/prepare_ampc.py

banner "PART 2.1  Deriving the box from the reference ligand"
$PYTHON ch09_first_run/scripts/derive_box.py

banner "PART 2.2  Docking STC into AmpC"
$PYTHON ch09_first_run/scripts/modes.py --system ampc

echo
echo "Synthetic results:  ch09_first_run/outputs/synthetic/"
echo "AmpC results:       ch09_first_run/outputs/ampc/"
echo "Expected:           ch09_first_run/outputs/expected/results.md"
