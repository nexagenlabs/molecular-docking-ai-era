#!/usr/bin/env bash
# The GNINA rescoring pipeline. Written to be run; not runnable here.
#
#   bash ch16_rescoring/scripts/rescore_with_gnina.sh
#
# GNINA is a compiled binary with a CUDA dependency. It is not on PyPI, there
# is no Windows build, and it wants a GPU. This script attempts it once and
# then says so rather than pretending.
set -euo pipefail

cd "$(dirname "$0")/../.."

RECEPTOR="ch17_validation/outputs/work/1L2S_receptor.pdbqt"
LIGAND="ch17_validation/outputs/work/1L2S_pose.pdbqt"

if ! command -v gnina >/dev/null 2>&1; then
  cat >&2 <<'MSG'
gnina is not installed, so this pipeline cannot run here.

  What it needs:   a compiled gnina binary and, in practice, a CUDA GPU
  Where it is not: PyPI, conda-forge, and Windows
  How to get it:   https://github.com/gnina/gnina  (prebuilt binary or Docker)

The command this chapter would run:

  gnina --receptor RECEPTOR.pdbqt \
        --ligand LIGAND.pdbqt \
        --autobox_ligand LIGAND.pdbqt \
        --cnn_scoring rescore \
        --seed 42 \
        --out rescored.sdf

  --cnn_scoring rescore   keeps Vina's poses and rescores them with the CNN,
                          which is the comparison the LIT-PCBA numbers are
                          from. --cnn_scoring all would also redo the search
                          and answer a different question.
  --seed 42               GNINA inherits Vina's default-seed behaviour, so
                          the same rule applies: set it and record it.

Nothing here is simulated. See ch16_rescoring/README.md and PROGRESS.md.
MSG
  exit 3
fi

echo "gnina found: $(gnina --version | head -1)"
gnina --receptor "$RECEPTOR" \
      --ligand "$LIGAND" \
      --autobox_ligand "$LIGAND" \
      --cnn_scoring rescore \
      --seed 42 \
      --out ch16_rescoring/outputs/rescored.sdf
