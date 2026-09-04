#!/usr/bin/env python3
"""Build the synthetic system behind Chapter 9's timing and box-size numbers.

    python ch09_first_run/scripts/make_test_system.py [outdir]

Deliberately not AmpC: a ten-heavy-atom ligand inside a crude shell of carbon
atoms, so the measurements are cheap and anyone can repeat them in seconds.
Docking STC into AmpC gives entirely different scores and they must not be
compared against these. The AmpC run is the second half of this chapter.

Writes lig.sdf (with explicit hydrogens) and rec.pdbqt into the output
directory, which defaults to ch09_first_run/outputs/synthetic.
"""
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

CH = Path(__file__).resolve().parent.parent
DEFAULT_OUT = CH / "outputs" / "synthetic"

LIGAND_SMILES = "c1ccccc1C(=O)NC"     # N-methylbenzamide, 10 heavy atoms
EMBED_SEED = 11
SHELL_ATOMS = 140
SHELL_SEED = 3
SHELL_MIN, SHELL_SPAN = 9.0, 1.5      # radius 9.0-10.5 A, centred on the origin


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)

    # -- ligand ------------------------------------------------------------
    # The hydrogens stay in the file. Meeko requires explicit hydrogens and
    # writes no PDBQT at all without them -- it reports an error and exits 0,
    # so a pipeline that does not check for the output file carries on happily
    # with the previous run's ligand.
    mol = Chem.AddHs(Chem.MolFromSmiles(LIGAND_SMILES))
    AllChem.EmbedMolecule(mol, randomSeed=EMBED_SEED)
    AllChem.MMFFOptimizeMolecule(mol)
    Chem.MolToMolFile(mol, str(out / "lig.sdf"))

    # -- receptor ----------------------------------------------------------
    # Carbons scattered on a spherical shell: not a protein, and not meant to
    # look like one. numpy's PCG64 stream is portable, so this file is
    # byte-identical on every platform -- which is what makes it usable as a
    # control when a score differs and the cause has to be found.
    rng = np.random.default_rng(SHELL_SEED)
    lines = []
    for i in range(SHELL_ATOMS):
        v = rng.normal(size=3)
        v /= np.linalg.norm(v)
        p = v * (SHELL_MIN + rng.uniform(0, SHELL_SPAN))
        lines.append("ATOM  %5d  C   REC A   1    %8.3f%8.3f%8.3f  1.00  0.00     0.000 C"
                     % (i + 1, p[0], p[1], p[2]))
    # newline="\n" explicitly. Python's text mode writes CRLF on Windows, and
    # then the portable half of this system would have a different digest on
    # every platform -- which would destroy its usefulness as the control when
    # a score differs and the cause has to be found.
    (out / "rec.pdbqt").write_text("\n".join(lines) + "\nTER\n", newline="\n", encoding="utf-8")

    heavy = Chem.RemoveHs(mol).GetNumAtoms()
    print("receptor: %d atoms on a %.1f-%.1f A shell" % (SHELL_ATOMS, SHELL_MIN,
                                                         SHELL_MIN + SHELL_SPAN))
    print("ligand:   %d heavy atoms, %d with hydrogens, embed seed %d"
          % (heavy, mol.GetNumAtoms(), EMBED_SEED))
    print("wrote %s and %s" % (out / "lig.sdf", out / "rec.pdbqt"))


if __name__ == "__main__":
    main()
