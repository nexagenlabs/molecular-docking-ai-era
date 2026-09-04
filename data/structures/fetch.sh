#!/usr/bin/env bash
# Download the four AmpC structures used throughout the book.
# Structures are fetched, not committed — see .gitignore.
#
#   bash data/structures/fetch.sh
set -euo pipefail

cd "$(dirname "$0")"

# 1L2S  1.94 A  redocking target        ligand STC, non-covalent
# 4JXS  1.90 A  cross-docking           ligand 18U, chain B only
# 4JXV  1.76 A  cross-docking           ligand 1MU, two altlocs
# 1GA9  2.10 A  EXCLUDED from docking   ligand ETP, covalent to Ser64 OG
#       (1GA9 is still fetched: Chapter 10's torsion analysis uses all four
#        structures, eight chains. The exclusion is a docking decision.)
for pdb in 1L2S 4JXS 4JXV 1GA9; do
  if [ -f "${pdb}.pdb" ]; then
    echo "${pdb}.pdb already present, skipping"
    continue
  fi
  echo "fetching ${pdb}"
  curl -fsSL -o "${pdb}.pdb" "https://files.rcsb.org/download/${pdb}.pdb"
done

echo
echo "Checksums (record these in your reproducibility record):"
sha256sum 1L2S.pdb 4JXS.pdb 4JXV.pdb 1GA9.pdb
