# Chapter 8 — expected results

RDKit ETKDGv3, 300 attempts, `pruneRmsThresh=0.5`, seeds 1 / 7 / 42 / 99 / 2026.
**Conformers are generated from the deprotonated form** — protonation comes
first, and the search runs on the species that will actually be docked.

## Charges — must match everywhere

| Ligand | Drawn | At pH 7.4 |
|---|---|---|
| STC | 0 | **−1** |
| 18U | 0 | **−2** |
| 1MU | 0 | **−2** |

A mismatch here is a hard failure, not a warning. The series spans two charge
states, so getting one wrong corrupts the ranking rather than shifting it.

## Rotatable bonds — must match everywhere

STC 4, 18U 6, 1MU 7.

## Conformer counts — exact on Linux

| Ligand | Deprotonated form (the book) | Neutral form, for comparison |
|---|---|---|
| STC | **15, 15, 16, 16, 16** | 17, 16, 15, 16, 15 |
| 18U | **9, 9, 12, 11, 8** | 10, 14, 9, 9, 9 |
| 1MU | **33, 35, 33, 28, 37** | 33, 39, 33, 30, 40 |

Counts do **not** track rotatable-bond count: 18U has two more rotatable bonds
than STC and yields fewer conformers. That is the chapter's point and must not
be "fixed".

The neutral column is not an alternative answer. It is the same search run on
the molecule as drawn, and it is there so that the table can say which form
produced which numbers — a conformer count published without its protonation
state cannot be reproduced.

The counts are **build-dependent**. On Windows, RDKit 2026.3.5 reproduces
**twelve of the fifteen** — the whole STC row included — and differs on three:
9, 9, **11**, 11, 8 for 18U and 33, 35, 33, **29**, **34** for 1MU. That is the
same build-level difference that moves the Chapter 9 docking scores. Neither
platform is wrong; the protocol is what has to be recorded, and the platform
with it. Record a mismatch rather than tuning to it.

## Stereochemistry

Preserved across an SDF round trip for all three. They are achiral, so this
passes trivially — it is kept as the guard for a chiral analogue later.
