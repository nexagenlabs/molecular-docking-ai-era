# Chapter 17 — expected results

Mode 1, symmetry-corrected, heavy atoms, **no superposition**, seed 42,
exhaustiveness 32:

| Entry | Ligand | Best affinity | RMSD to crystal pose | Best over 9 modes |
|---|---|---|---|---|
| 1L2S | STC | −7.377 | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | −7.805 | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | −8.131 | **10.526 Å** | 10.371 Å (mode 4) |

These are the values now printed in the book's Chapter 17, in place of its
`[x]` placeholders, along with the mode-3 finding and the 5.9 Å chain
sensitivity below. They were measured on Windows; see the platform note in
Chapter 9 for why the underlying scores are build-dependent.

## What must hold everywhere

The RMSD numbers will move between platforms. These will not:

- The ligand copy is chosen at **2.70 Å** from Ser64 OG, and the copy at
  **22.72 Å** appears among the candidates and is discarded.
- Every unused HETATM group is reported by name.
- The RMSD is computed with `minimize=False`, heavy atoms only,
  symmetry-corrected. A record that does not say superposition was off contains
  an RMSD that means nothing.
- No RMSD is exactly zero. A zero here means superposition crept in.

## The chain sensitivity check

| Entry | Protocol chain | RMSD | Alternative | RMSD | Difference |
|---|---|---|---|---|---|
| 4JXV | A | 10.526 Å | B | 4.609 Å | **5.917 Å** |

Chain A was chosen because it needs one altloc decision instead of two. That
reasoning sounds cosmetic; the difference is three times the 2 Å threshold the
whole exercise is judged against.

## Reading the result honestly

One pass, one near-miss whose correct pose is ranked third, one failure. The
best *affinity* is inversely ordered against the RMSD: 4JXV scores best and is
wrong by 10 Å. A score is not evidence of a pose, and this table is the
demonstration.
