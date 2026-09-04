# Chapter 26 — case study

Three reproduction tests, each with a published answer, so each can fail. A
protocol that cannot fail has not been validated.

## Run

```bash
bash ch26_case_study/run.sh
```

Nine docking runs at exhaustiveness 32 — allow about five minutes.

## Test 1 — redock 1L2S

| | RMSD |
|---|---|
| This run | **1.114 Å** |
| Original authors | 1.75 and 1.87 Å |

Under 2 Å either way, which is the criterion that matters. Reproducing a
published number to two decimals would be surprising and slightly suspicious;
reproducing the **conclusion** is what a reproduction test is for.

## Test 2 — cross-docking

Every ligand into every receptor. The diagonal is a redock; the off-diagonal is
what prospective work actually looks like.

| Receptor | STC | 18U | 1MU |
|---|---|---|---|
| 1L2S | **−7.377** (RMSD 1.114 Å) | −8.090 | −7.916 |
| 4JXS | −6.806 | **−7.805** (RMSD 2.999 Å) | −7.781 |
| 4JXV | −7.315 | −7.969 | **−8.131** (RMSD 10.526 Å) |

| Ligand | Best receptor | Native receptor | Prefers its own? |
|---|---|---|---|
| STC | 1L2S | 1L2S | yes |
| 18U | 1L2S | 4JXS | **no** |
| 1MU | 4JXV | 4JXV | yes |

**18U scores better in 1L2S than in the structure it was crystallised in.**
That is the finding: the receptor conformations differ more than the ligands
do, which is exactly why cross-docking is harder than redocking and why a
redock alone does not validate a protocol.

Note also that 4JXV gives the best score in the whole matrix (−8.131) on the
run with the **worst** RMSD (10.526 Å). Score and correctness are not the same
axis.

## Test 3 — ranking the series

| Ligand | Docking score | Ki (ChEMBL) | Ki (PDBbind) | ΔG from Ki |
|---|---|---|---|---|
| STC | −7.377 | 26 µM | 26 µM | −6.25 kcal/mol |
| 18U | −8.090 | 18 µM | 18 µM | −6.47 kcal/mol |
| 1MU | −7.916 | 26 µM | 31 µM | −6.15 to −6.25 kcal/mol |

| Ordering | |
|---|---|
| By docking score | 18U < 1MU < STC |
| By Ki (ChEMBL) | 18U < 1MU = STC |
| By Ki (PDBbind) | 18U < STC < 1MU |

Docking gets 18U right — it is the tightest binder by both sources. Beyond
that, **there is no reliable ranking here to reproduce.**

- The series spans 18–31 µM: a factor of 1.7, or **0.32 kcal/mol**.
- ChEMBL does not order STC against 1MU at all; both are 26 µM.
- The two sources disagree about 1MU by *more* than the gap between STC and
  1MU.

No scoring function resolves 0.32 kcal/mol. A method that appeared to would be
reporting its own noise, and getting the "right" order from three compounds
inside that spread is a coin flip with two outcomes.

That is a result, not a failed test. A congeneric series this tight is the
wrong instrument for asking whether a method can rank, and finding that out
before running the experiment is much cheaper than finding it out after.

## On converting affinities

ΔG is computed **from** Ki here, which is arithmetic. The reverse — reading a
Ki off a docking score — is not, and neither is converting between Ki, IC50 and
Kd. No such conversion appears anywhere in this repository. ETP's 83 nM was
measured with a different substrate and buffer and is not comparable to the
values above, which is one of the reasons 1GA9 is excluded.
