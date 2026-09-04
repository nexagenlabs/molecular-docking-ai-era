# Chapter 4 — expected results

Each charged ligand written out to a format, read back, and compared with the
original by canonical SMILES, formal charge and atom order.

| Format | Charge | Bond orders | Stereochemistry | Atom order |
|---|---|---|---|---|
| **PDB** | preserved | preserved | preserved | preserved |
| **MOL2** | preserved | preserved | preserved | preserved |
| **PDBQT** | **lost** — −2 comes back as 0 | — | — | **changed** |
| **XYZ** | **lost** | — | — | preserved |

All three ligands behave identically, so the result is a property of the
formats rather than of one molecule.

## The folklore is out of date

"PDB destroys bond orders and stereochemistry" was true of tools that read only
the CONECT records. Open Babel re-perceives chemistry from the 3D coordinates,
and a PDB round trip returns the same molecule, charge included. The README
says so explicitly, because the folklore is still repeated.

## PDBQT is the format that actually loses information

And it is the one docking uses. Two separate problems:

- **The charge loss** matters because the charges differ across this series
  (STC −1, 18U and 1MU −2). Losing them is not a uniform shift — it is a
  different error per ligand, which corrupts the ranking rather than moving it.
- **The reordering** matters because it silently breaks any RMSD computed
  against the original file. The numbers still come out. They are just
  measuring distances between mismatched atoms.

Keep an SDF as the reference copy and convert outward only.

## Open Babel version

Produced with **Open Babel 3.1.0**, not the pinned 3.2.1: `openbabel-wheel`
ships no 3.2.1 build for Windows. Every conclusion above is unchanged, which is
worth stating — the version difference was recorded before the run, not after
it turned out not to matter.
