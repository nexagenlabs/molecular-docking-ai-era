# Chapter 9 — expected results

The values printed in the book, and what this repository's script actually
produces. Read the status line on each one before you compare your own run.

| Demonstration | Status |
|---|---|
| 1. The seed | **reproduced** |
| 2. Exhaustiveness | **reproduced in ratio**, absolute times are per-machine |
| 3. Box size | **behaviour reproduced, absolute scores do not match — unresolved** |
| 4. Mode 1's RMSD | **reproduced** |

---

## 1. The seed

**Book:** seed 0 twice → different. Seed 42 twice → byte-identical.

**Reproduced.** On the reference machine below:

| Run | Best affinity | Pose digest |
|---|---|---|
| seed 0, run 1 | −7.407 | `d153513c9ae318f1` |
| seed 0, run 2 | −7.390 | `2d189a4ae5d5a25e` |
| seed 42, run 1 | −7.384 | `d4a1693823dc0ed7` |
| seed 42, run 2 | −7.384 | `d4a1693823dc0ed7` |

Your affinities will differ if your inputs differ; what must hold is the
*pattern* — two digests at seed 0, one at seed 42.

## 2. Exhaustiveness

**Book:** 8 → 3.4 s, 32 → 14.2 s on 4 cores, a factor of 4.2.

**Reproduced in ratio.** This machine: 7.27 s and 26.96 s on 4 cores, a factor
of **3.7**. Wall time is a property of the machine and will not match; the
factor is the claim that travels, and it is not the factor of 4 that the
exhaustiveness ratio suggests, because part of the run is fixed cost.

## 3. Box size

**Book:** cube edges 20 / 12 / 8 Å → best score **−4.905 / −4.911 / −2.748**,
with no error raised at any size.

**Behaviour reproduced. Absolute scores do not match, and the discrepancy is
unresolved — do not assume either side is right.**

| Cube edge | Book | This repository |
|---|---|---|
| 20 Å | −4.905 | −7.384 |
| 12 Å | −4.911 | −7.410 |
| 8 Å | −2.748 | −6.837 |

What does reproduce, and is the chapter's actual point:

- **No error is raised at any size**, exit status 0 throughout. The undersized
  box returns a number that looks exactly like a result.
- **20 Å and 12 Å agree** — 0.006 apart in the book, 0.026 here. Once the box
  covers the pocket, making it larger buys nothing.
- **8 Å is worse than both.** STC's longest interatomic distance is 9.41 Å, so
  an 8 Å cube cannot hold it in every orientation.

What does not reproduce is the size of the collapse at 8 Å: 2.16 kcal/mol in
the book against 0.55 kcal/mol here, on top of a uniform offset of roughly
2.5 kcal/mol across all three sizes.

### What has been ruled out

Measured, not guessed:

| Hypothesis | Result |
|---|---|
| The bridging waters were kept | Rejected. Keeping HOH 403 and 481 gives −7.361 against −7.384; a 0.023 difference cannot account for 2.5. |
| The box was centred on a naive centroid over all three STC copies | Rejected. That centre is 24.76 Å from the nearest Ser64 OG, and gives −7.712 / −5.417 / −4.529 — a monotone decline, not the book's two-equal-then-collapse shape. |

### What is still open

The book's Chapter 9 protocol is not fully specified in `CLAUDE.md`. Any of
these would move the absolute scores, and none can be settled from this side:

1. **Receptor preparation route.** This script uses meeko 0.8.0. A receptor
   prepared with AutoDockTools' `prepare_receptor4.py` or with Open Babel gets
   different atom typing, and a systematic offset of a couple of kcal/mol is
   the expected size of that difference.
2. **Box centre.** Reproducing the two-equal-then-collapse shape needs a centre
   where a 12 Å cube still covers the pocket and an 8 Å one clips it. The
   centroid of STC B/2115 is not it.
3. **Which ligand conformer and which chain.** This script docks the committed
   `data/ligands/STC.sdf` into chain B.
4. **Exhaustiveness for the box sweep**, which the book does not state. This
   script uses Vina's default, 8.

Until one of those is settled, treat the book's three numbers and this
repository's three numbers as measurements of two different protocols, not as a
disagreement about one.

## 4. Mode 1's RMSD

**Book:** mode 1 always reports RMSD `0.000 0.000`.

**Reproduced.** The column is distance from mode 1, so mode 1's distance from
itself is zero by construction. It is not a comparison with the crystal pose,
and reading it as one is the most common way a docking run appears to validate
itself. Chapter 17 measures the distance that matters — spyrmsd,
symmetry-corrected, heavy atoms, no superposition.

---

## Reference machine

These numbers were produced on:

| | |
|---|---|
| Vina | AutoDock Vina v1.2.7 (official Windows binary) |
| Platform | Windows 11 (10.0.26200) |
| Python | 3.12.10 |
| RDKit / meeko | 2026.3.5 / 0.8.0 |
| Cores | 4 |
| Receptor | 1L2S chain B, all waters deleted, altloc A, ten REMARK 470 side chains typed as alanine |
| Ligand | `data/ligands/STC.sdf`, formal charge −1 |
| Box centre | 79.802, 5.352, 29.948 (centroid of STC B/2115) |

The book's own numbers came from pip on Ubuntu, Python 3.12.3. See
`environment/README.md`.
