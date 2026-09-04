# Chapter 4 — file formats

What each format destroys, measured rather than assumed.

## Run

```bash
bash ch04_formats/run.sh
```

Each charged ligand is written out to a format, read back, and compared with
the original by canonical SMILES, formal charge and heavy-atom order.

## The result

| Format | Charge | Bond orders | Stereochemistry | Atom order |
|---|---|---|---|---|
| **PDB** | preserved | preserved | preserved | preserved |
| **MOL2** | preserved | preserved | preserved | preserved |
| **PDBQT** | **lost** — the 18U dianion returns neutral | — | — | **changed** |
| **XYZ** | **lost** | — | — | preserved |

All three ligands behave the same way, so this is a property of the formats
rather than of one awkward molecule.

## The folklore is out of date

**"PDB destroys bond orders and stereochemistry" is no longer true**, and this
chapter exists partly to say so. It was true of tools that read only the CONECT
records. Open Babel re-perceives chemistry from the 3D coordinates, and a PDB
round trip here returns the same molecule — canonical SMILES identical, formal
charge identical, atom order identical.

If you have been avoiding PDB for chemistry reasons, the reason expired.

## PDBQT is the format that actually loses information

And it is the one docking uses. Two separate failures, and they break different
things:

- **Charge loss.** The 18U dianion goes in at −2 and comes back at 0. This
  matters *because the charges differ across the series* — STC is −1, 18U and
  1MU are −2. Losing them is not a uniform shift, it is a different error for
  each ligand, so it corrupts the ranking rather than moving it. A shifted
  ranking is still the right order; a corrupted one is not, and it looks
  exactly the same.
- **Reordering.** The atom order changes. Any RMSD computed against the
  original file is then measuring distances between mismatched atoms. It still
  produces numbers. They are simply not the numbers you asked for.

**So keep an SDF as the reference copy and convert outward only.** Never read a
PDBQT back in and treat it as the ligand you started with. That is the rule
`data/ligands/` follows, and it is why Chapter 17 measures RMSD against the SDF
rather than against the pose file.

## Open Babel version

These results are from **Open Babel 3.1.0**, not the pinned 3.2.1 —
`openbabel-wheel` ships no 3.2.1 build for Windows. The version difference was
recorded as a risk to this chapter before the run, since these results are
literally Open Babel's output. It changed none of them.
