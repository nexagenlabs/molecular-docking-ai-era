# Chapter 3 — databases, cross-checked against themselves

Resolution and R-free taken from two independent places: the RCSB REST
API, and the header of the coordinate file this repository downloaded.

| Entry | Resolution (API / file) | R-free (API / file) | Agree? |
|---|---|---|---|
| 1L2S | 1.94 / 1.94 | 0.207 / 0.207 | yes |
| 4JXS | 1.90 / 1.90 | 0.212 / 0.212 | yes |
| 4JXV | 1.76 / 1.76 | 0.232 / 0.232 | yes |
| 1GA9 | 2.10 / 2.10 | 0.249 / 0.249 | yes |

## Ligands, against the PDB chemical component dictionary

| Ligand | Formula | Same neutral skeleton? |
|---|---|---|
| STC | C11 H8 Cl N O4 S2 | yes |
| 18U | C13 H11 N O6 S2 | yes |
| 1MU | C14 H13 N O6 S2 | yes |
| ETP | C16 H14 B N O6 S3 | — |

The comparison is against the **neutral** skeleton on purpose. The
PDB component describes the molecule as modelled in the crystal,
which carries no protonation state for pH 7.4. This repository docks
STC at −1 and 18U and 1MU at −2. Those are different molecules, and
the difference is the subject of Chapter 8 — so the check here is
that the *skeleton* matches, and the charge is expected to differ.

## Affinity

| Ligand | ChEMBL | PDBbind | |
|---|---|---|---|
| STC | 26 µM | 26 µM | agree |
| 18U | 18 µM | 18 µM | agree |
| 1MU | 26 µM | 31 µM | **disagree** |

Both 1MU values are carried through to the end rather than one being
chosen. Chapter 26 shows why that matters: the disagreement between the
sources is larger than the gap between 1MU and STC that a method would
have to resolve to rank them.

**ETP is 83 nM**, measured with a different substrate and buffer. It is
not comparable to the values above and is never converted. No conversion
between Ki, IC50 and Kd happens anywhere in this repository.
