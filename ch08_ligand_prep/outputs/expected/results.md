# Chapter 8 — expected results

RDKit ETKDGv3, 300 attempts, `pruneRmsThresh=0.5`, seeds 1 / 7 / 42 / 99 / 2026.
**Conformers are generated from the neutral (drawn) form**; protonation is
applied afterwards, when the ligand is written for docking.

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

| Ligand | Neutral form (the book) | Docked form, for comparison |
|---|---|---|
| STC | **17, 16, 15, 16, 15** | 15, 15, 16, 16, 16 |
| 18U | **10, 14, 9, 9, 9** | 9, 9, 12, 11, 8 |
| 1MU | **33, 39, 33, 30, 40** | 33, 35, 33, 28, 37 |

Counts do **not** track rotatable-bond count: 18U has two more rotatable bonds
than STC and yields fewer conformers. That is the chapter's point and must not
be "fixed".

On Windows, RDKit 2026.3.5 gives 16, 16, 15, 16, 15 for STC and differs by one
or two elsewhere — the same build-level difference that moves the Chapter 9
docking scores. Neither platform is wrong; the protocol is what has to be
recorded, and the platform with it.

## Stereochemistry

Preserved across an SDF round trip for all three. They are achiral, so this
passes trivially — it is kept as the guard for a chiral analogue later.
