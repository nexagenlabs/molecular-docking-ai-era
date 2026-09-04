# Ligand reference copies

The congeneric series, sharing an 18-heavy-atom core.

| Ligand | SMILES | Charge at pH 7.4 | Ki |
|---|---|---|---|
| STC | `c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)O)Cl` | −1 | 26 µM |
| 18U | `c1cc(ccc1CNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O` | −2 | 18 µM |
| 1MU | `c1cc(ccc1CCNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O` | −2 | 26 µM (ChEMBL) / 31 µM (PDBbind) |

**The 1MU value disagrees between sources. Report both; do not pick one.**

**The charges differ across the series.** Docking the drawn neutral forms gets
every member wrong, and by a different amount for each — which is worse than a
uniform error, because it corrupts the ranking rather than shifting it.

**Do not convert between Ki, IC50 and Kd.** ETP's 83 nM was measured with a
different substrate and buffer and is not comparable to the values above.

The docked forms are the SMILES above with every carboxylic acid deprotonated.
The aryl sulfonamide N-H has a pKa near 10 and stays neutral at pH 7.4, so the
carboxylates account for the whole of the -1 and -2.

## The files

`STC.sdf`, `18U.sdf` and `1MU.sdf` are the reference copies and they are
committed, so every reader measures RMSD against a byte-identical file rather
than against whatever their RDKit produced. They are 3D, charge-explicit, and
carry their provenance in SDF tags (SMILES, charge, Ki, PDB entry, embedding
seed, force field, RDKit version).

`generate.py` is how they were made, and how that stays auditable:

```bash
python data/ligands/generate.py            # write the SDFs
python data/ligands/generate.py --check    # rebuild in memory, compare, write nothing
```

`--check` compares canonical SMILES, formal charge, atom count and coordinates
against the committed files. **It must be run under the pinned environment**
(`environment/README.md`) -- a coordinate mismatch under a different RDKit is
expected, and is exactly why the SDFs are committed rather than generated on
the reader's machine.

SDFs are the reference copies: PDBQT loses formal charge and reorders atoms, so
conversion is outward only, never round-tripped.

## Provenance of the committed copies

Built with rdkit 2026.3.5 — the pinned version — but on **Windows 11, Python
3.12.10**, not the Ubuntu 3.12.3 machine that produced the book's numbers. Each
SDF carries `rdkit_version`, `python_version` and `platform` tags, so the
provenance is in the file rather than only in this README.

Two independent checks that the copies are right:

- Heavy-atom counts are **19 / 22 / 23** for STC / 18U / 1MU, matching the atom
  counts of the crystallographic ligands in 1L2S, 4JXS and 4JXV exactly.
- Formal charge is asserted against the table above during generation, not
  assumed — a SMILES that fails to deprotonate stops the script.

If a rebuild under Ubuntu 3.12.3 gives different coordinates, that is worth
knowing and worth recording here: replace these copies with those, and say so.
