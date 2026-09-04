# Chapter 26 — case study: three reproduction tests

AutoDock Vina v1.2.7, seed 42, exhaustiveness 32.

## The cross-docking matrix

Affinity in kcal/mol; the diagonal is a redock and carries an RMSD.

| Receptor | STC | 18U | 1MU |
|---|---|---|---|
| 1L2S | **-7.377** (RMSD 1.114 Å) | -8.090 | -7.916 |
| 4JXS | -6.806 | **-7.805** (RMSD 2.999 Å) | -7.781 |
| 4JXV | -7.315 | -7.969 | **-8.131** (RMSD 10.526 Å) |

## Test 1 — redock 1L2S

| | RMSD |
|---|---|
| This run | **1.114 Å** |
| Original authors | 1.75 and 1.87 Å |

Under 2 Å either way, which is the criterion that matters. Reproducing
a published number to two decimals would be surprising; reproducing the
*conclusion* is what a reproduction test is for.

## Test 2 — cross-docking

| Ligand | Best receptor | Native receptor | Prefers its own? |
|---|---|---|---|
| STC | 1L2S | 1L2S | yes |
| 18U | 1L2S | 4JXS | **no** |
| 1MU | 4JXV | 4JXV | yes |

A ligand that does not score best in the structure it was crystallised
in is telling you the receptor conformations differ more than the
ligands do — which is the whole reason cross-docking is harder than
redocking, and the reason a redock alone does not validate a protocol.

## Test 3 — ranking the series

| Ligand | Docking score | Ki (ChEMBL) | Ki (PDBbind) | ΔG from Ki |
|---|---|---|---|---|
| STC | -7.377 | 26 µM | 26 µM | -6.25 to -6.25 kcal/mol |
| 18U | -8.090 | 18 µM | 18 µM | -6.47 to -6.47 kcal/mol |
| 1MU | -7.916 | 26 µM | 31 µM | -6.15 to -6.25 kcal/mol |

| Ordering | |
|---|---|
| By docking score | 18U < 1MU < STC |
| By Ki (ChEMBL) | 18U < 1MU = STC |
| By Ki (PDBbind) | 18U < STC < 1MU |

ChEMBL puts STC and 1MU at the same 26 µM, so it does not order them at
all. A sort function will still return one before the other, and the
result reads as a ranking the data does not contain.

**There is no reliable ranking here to reproduce.** The series spans
18–31 µM — a factor of 1.7, or **0.32 kcal/mol** — and the two sources
disagree about 1MU by more than the gap between STC and 1MU. No scoring
function resolves 0.3 kcal/mol, and a method that appeared to would be
reporting its own noise.

That is a result, not a failure of the test. A congeneric series this
tight is the wrong instrument for measuring whether a method can rank,
and finding that out before running the experiment is cheaper than
finding it out afterwards.
