# Chapter 17 — validation

Does the protocol reproduce the crystallographic pose? This is the most
load-bearing script in the repository: everything else is a preparation step
for a number that only means something if this one works.

## Run

```bash
bash ch17_validation/run.sh
```

Takes about three minutes. Writes `outputs/validation.json` and
`outputs/validation_record.md`.

## What it does

1. Fetches 1L2S, 4JXS and 4JXV from `files.rcsb.org`.
2. Separates receptor from ligand, and **prints every HETATM group it did not
   use**, by name and count.
3. Selects the ligand copy **by distance to Ser64 OG**, not by file order.
4. Derives the box from the crystallographic ligand's centroid with 8 Å
   padding.
5. Docks at **seed 42, exhaustiveness 32**.
6. Computes symmetry-corrected heavy-atom RMSD **without superposition**.
7. Emits `validation_record.md` in the format of Chapter 20's protocol record.

The ligand that gets docked is a **generated** conformer from
`data/ligands/`, not the crystal pose. Docking the crystal conformer back
would test the search algorithm and nothing else.

## `--minimize` must never be used

```bash
python -m spyrmsd ref.sdf pose.sdf              # correct
python -m spyrmsd --minimize ref.sdf pose.sdf   # WRONG — never
```

`--minimize` superimposes the two structures before measuring, which discards
exactly the thing a redock tests. A pose displaced 3.0 Å returns `3.00000`
without the flag and `0.00000` with it. **The flag makes every validation
pass**, which is why `tests/test_gotchas.py` fails the build if the string
appears anywhere in this repository.

This script calls spyrmsd's `symmrmsd` with `minimize=False` and records that
choice in the output, so a reader can check it rather than trust it.

## The three RMSD values

Mode 1, symmetry-corrected, heavy atoms, no superposition:

| Entry | Ligand | Best affinity | **RMSD** | Best over 9 modes |
|---|---|---|---|---|
| 1L2S | STC | −7.377 | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | −7.805 | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | −8.131 | **10.526 Å** | 10.371 Å (mode 4) |

**These fill the `[x]` placeholders in the book's Chapter 17.**

Read against the usual 2 Å criterion: one clear pass, one failure whose correct
pose is present but ranked third, and one outright failure. That is a more
useful result than three passes would have been. Note also that the best
affinity is *inversely* ordered against the RMSD — 4JXV scores best and is
wrong by 10 Å. A score is not evidence of a pose.

## An arbitrary decision worth 6 Å

4JXV holds 1MU in both chains: A/402 as a single conformer, B/401 modelled in
two altlocs. Chain A was chosen a priori because it costs one decision instead
of two — which sounds like tidiness rather than science.

The script runs the alternative as a sensitivity check:

| Protocol chain | RMSD | Alternative chain | RMSD | Difference |
|---|---|---|---|---|
| A | 10.526 Å | B | 4.609 Å | **5.917 Å** |

Both fail the 2 Å criterion, so the conclusion does not change — but the
decision moved the number by three times that threshold. **A preparation
decision is not cosmetic because the reasoning for it sounded cosmetic.** This
is the argument for the protocol record: not that the choice was wrong, but
that a reader cannot evaluate the result without knowing it was made.

## Recorded decisions

- **1L2S chain B** — chain A is missing Lys290–Ala292.
- **4JXS chain B** — the inhibitor is in chain B only; chain A holds phosphate.
- **4JXV chain A** — see above.
- **All waters deleted**, including HOH 403 and 481 in 1L2S chain B, which
  bridge the ligand to the protein at 2.68 and 2.70 Å. This is the usual
  default and it can put the crystallographic pose out of reach.
- **Disordered side chains typed down** to what the file actually contains,
  where the remaining atoms are exactly alanine's or glycine's. Anything else
  **stops the run** rather than being guessed at.
- **1GA9 excluded** — ETP is covalently bound to Ser64 OG (`LINK`, 1.64 Å in
  chain A, 1.62 Å in chain B). Non-covalent docking cannot represent that bond.
  The exclusion is a modelling decision and is recorded as one.

## Platform

The RMSD values above are from Windows. The docking scores underneath them are
build-dependent (see Chapter 9), so expect small differences on Linux and
larger ones wherever a pose ranking flips — 4JXS's correct pose sits at mode 3,
0.09 kcal/mol below mode 2, which is well inside the range a different build
can move.
