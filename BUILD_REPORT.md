# Build report

What was built, what runs, what could not run here, and every value that
differed from `CLAUDE.md` §6 with an assessment of which side is wrong.

Built on Windows 11, Python 3.12.10, against `CLAUDE.md` and `SESSION_PLAN.md`.

---

## Status

| | |
|---|---|
| Chapter directories | 25 of 25, each with `README.md`, `run.sh`, `outputs/expected/` |
| Chapters that run end to end | **25 of 25** |
| Tests | **75 passed, 15 xfailed, 0 failed** (4m 06s) |
| Commits | 25 |
| Scripts | 37 |
| Software that could not run here | 3 (GNINA, Boltz-2, PDBFixer) |
| `TODO(value)` remaining | none |

Every `run.sh` was executed from a clean state after the last commit. The five
docking chapters (ch06, ch09, ch12, ch17, ch26) take a few minutes each; the
rest are seconds.

---

## Values that differed from CLAUDE.md §6

Four disagreements. **Two were resolved in the book's favour, two remain open.**
No expected value was edited in either case.

### 1. ch09 box-size scores — resolved, platform

| | 20 Å | 12 Å | 8 Å |
|---|---|---|---|
| Book | −4.905 | −4.911 | −2.748 |
| **Native Linux (WSL, this machine)** | **−4.905** | **−4.911** | **−2.748** |
| Native Windows | −4.910 | −4.903 | −2.686 |
| Linux Vina, Windows-built ligand | −4.904 | −4.896 | −2.728 |

**The book is right.** Two independent causes, isolated by swapping one
component at a time: the Windows RDKit 2026.3.5 build MMFF-optimises to
different coordinates than the Linux build of the same version, and the Windows
Vina build scores differently even on identical input files. The receptor,
built from numpy's PCG64, is byte-identical across both — which is what made
the isolation possible.

**Consequence for the repository:** seed 42 is byte-identical *within* a build,
not across builds, and nothing in the log says which situation you are in.
Exact-value tests assert three decimals on Linux and xfail elsewhere with the
reason attached.

### 2. ch08 conformer counts — resolved, under-specified protocol

`CLAUDE.md` gives the ETKDGv3 settings but not which protonation state is
embedded. Docking the charged forms gave 15/15/16/16/16 for STC against the
book's 17/16/15/16/15 — wrong on **both** platforms, so not the build.

**Embedding the neutral (drawn) form reproduces all three rows exactly on
Linux:** 17/16/15/16/15, 10/14/9/9/9, 33/39/33/30/40.

**The book is right.** The order of operations is: search shape on the drawn
molecule, apply protonation when writing the ligand for docking. The chapter
now prints both columns, because a conformer table that does not say which form
produced it cannot be reproduced.

### 3. ch18 enrichment metrics — open, construction not recorded

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 45.0 | 11.0 | 0.555 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.8 | 0.059 |

`CLAUDE.md` gives the results without the construction, and everything
downstream of AUC depends on how the actives are arranged. Screen B is close;
screen A is not. A rank-based construction was also tried and reached BEDROC
0.5752 against 0.574 — nearer, still not exact, which is the signature of a
missing recipe rather than a missing calculation.

What reproduces and is checkable regardless: both AUCs at 0.758, BEDROC
agreeing with `rdkit.ML.Scoring.Scoring.CalcBEDROC` **to six decimals**, and
79.8% of the α=20 weight in the top 8% (analytic, exact).

**Not pursued further on purpose.** Fitting free parameters until four
published numbers appear produces a script that agrees with the book by
construction rather than by measurement.

### 4. ch21 MD window slopes — open, noise realisation not recorded

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | −0.150 | +0.113 |
| 10 ns | 1.47 Å | 1.42 Å | −0.010 | +0.015 |
| 100 ns | 1.90 Å | 1.80 Å | +0.007 | +0.004 |
| 1000 ns | 2.34 Å | 2.30 Å | +0.0004 | +0.0000 |

The decisive observation: **a monotone sum of exponentials cannot produce a
negative slope at all.** The book's two negative slopes come from noise in its
trajectory, so they are a property of one realisation with a seed nobody wrote
down. Fitting amplitudes *and* timescales jointly to all seven published
numbers leaves a residual of about 0.08 Å that will not reduce — the size that
noise would explain.

Means land within 0.1 Å and the chapter's actual claim reproduces: the 10 ns
answer is 38% below the 1000 ns one, against the book's 37%.

---

## Values confirmed against CLAUDE.md

Everything else in §6 and §1 reproduced, several by two independent routes:

- **All four structures' resolution and R-free** — from the coordinate file
  header *and* the RCSB REST API (ch03). 1.94/0.207, 1.90/0.212, 1.76/0.232,
  2.10/0.249.
- **Three STC copies in 1L2S** at 2.70, 2.70 and **22.72 Å** from Ser64 OG
  (ch05, ch17, ch20).
- **Chain A missing Lys290–Ala292; sole altloc Gln250** (ch05).
- **Bridging waters HOH 403 and 481** in chain B at 2.68 and 2.70 Å, contacting
  Asn346/Arg349 and Thr316/Lys315/Tyr150 respectively (ch05).
- **Nearest phosphate 7.83 Å**, in 4JXS; **1L2S contains none** (ch05).
- **1GA9 covalent LINK**, 1.64 Å chain A and 1.62 Å chain B, plus a K⁺ ion
  (ch05, `scripts/audit_structures.py`).
- **Formal charges** STC −1, 18U −2, 1MU −2, and rotatable bonds 4/6/7 (ch08).
- **PDB and MOL2 preserve charge, bond orders and stereochemistry; PDBQT
  returns the dianion neutral with the atom order changed; XYZ loses charge**
  (ch04) — and this held on Open Babel 3.1.0, not the pinned 3.2.1.
- **Gln120, Leu293 and Thr316** as the only rotamer-changing residues, with
  **eight** site residues inside 20° in every torsion (ch10).
- **Seed 0 twice differs; seed 42 twice is byte-identical** (ch09).
- **Mode 1 always reports RMSD 0.000 0.000** (ch09).
- **An undersized box raises no error** (ch09).
- **r² = 0.38 against FEP+ 0.52** (ch14).
- **UniProt = PDB + 16**, recovered from the sequences at 100% residue identity
  (ch06) and again from the mature-sequence frame check (ch13).
- **Exhaustiveness ratio 3.55** on the synthetic system (book 4.2, band 3–5).

---

## The three RMSD values for Chapter 17's placeholders

Mode 1, symmetry-corrected, heavy atoms, **no superposition**, seed 42,
exhaustiveness 32, measured on Windows:

| Entry | Ligand | Affinity | **RMSD** | Best over 9 modes |
|---|---|---|---|---|
| 1L2S | STC | −7.377 | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | −7.805 | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | −8.131 | **10.526 Å** | 10.371 Å (mode 4) |

One pass, one near-miss whose correct pose sits at mode 3, one failure. The
best affinity runs *inversely* to the RMSD — 4JXV scores best in the whole set
and is wrong by 10 Å.

**Chain sensitivity:** 4JXV chain A gives 10.526 Å, chain B gives 4.609 Å. The
chain was chosen because it needed one altloc decision instead of two, which
sounds cosmetic and moved the number by 5.9 Å.

---

## Software that could not run here

Pipelines written, attempted once, and documented. **No output was simulated.**

| Software | Chapter | Why not |
|---|---|---|
| **GNINA** | ch16 | Compiled binary, CUDA dependency, no PyPI or conda-forge package, no Windows build. `pip install gnina`: no distribution. |
| **Boltz-2** | ch13 | Installs, but needs a CUDA GPU and multi-GB weights — **and breaks the pinned environment on the way in** (below). |
| **PDBFixer** | ch05 | conda-forge only, pulls in OpenMM. Documented as the alternative to typing disordered side chains down to alanine; the code shown is not run. |

Each of the two scripts exits 3 with the exact command it would run, and ch13
writes and frame-checks its Boltz-2 input regardless, since that is the half a
reader can check without a GPU.

---

## The environment broke once, and was repaired

**`pip install boltz` silently downgraded the pinned environment.** It succeeds
on a CPU-only machine and pulls numpy down to 1.26.4, gemmi to 0.6.5 and scipy
to 1.13.1 — the three pins that ch08's conformer counts, ch17's RMSD and
meeko's PDBQT output all depend on. No error; pip resolved its own constraints.

Repaired immediately: boltz and its eighteen leftover dependencies uninstalled,
`numpy==2.4.4 gemmi==0.7.5 scipy>=1.17.1 rdkit==2026.3.5 meeko==0.8.0
spyrmsd==0.9.0` reinstalled, versions verified, and the **full suite re-run and
passing** before any further work.

Recorded in ch13's README as a reproducible property of that package rather
than as general advice: **install co-folding models in a separate
environment.**

`environment/resolved.txt` should be regenerated before release.

---

## Bugs the expected values caught

Each of these produced a plausible wrong answer rather than an error, and each
was caught by a value in `CLAUDE.md` rather than by review:

1. **R-free reported as 2647** (ch05). `FREE R VALUE TEST SET COUNT` sits a few
   lines from `FREE R VALUE`. The RCSB API sets the identical trap —
   `ls_number_reflns_R_free` beside `ls_R_factor_R_free` — so reaching for an
   API instead of a parser does not avoid it (ch03).
2. **Every structure at 2.00 Å** (ch05). `REMARK   2 RESOLUTION.` makes the
   first float on the line the remark number.
3. **Eight rotamer-changing residues instead of three** (ch10). All five extras
   were terminal-group artefacts: Asn χ2 and Gln χ3 record which way round an
   amide was modelled, not which way it points.
4. **A missing hydrogen made meeko write nothing and exit 0** (ch09). The
   supplied `make_test_system.py` stripped hydrogens against the recipe; a
   pipeline trusting the exit status docks whatever the previous run left.
5. **The mature-sequence offset written as PDB rather than PDB − 3** (ch13),
   caught by the script's own frame check. Two offsets compose there.
6. **A tie printed as an ordering** (ch26). `sorted()` put STC before 1MU when
   ChEMBL gives both 26 µM.
7. **A side-chain count produced by a nonsense expression** that returned the
   right answer by accident (ch27).
8. **A conclusion asserted rather than computed** (ch07, ch21). One printed
   "every window passes" while a window was visibly still rising; the other
   printed "the result list is not" on the strength of 8/9 against 9/9.

---

## Deviations from CLAUDE.md and SESSION_PLAN.md

- **Notebooks are scripts.** ch14 and ch18 are Python scripts writing a
  Markdown report and a PNG. A script runs in CI and fails loudly; a notebook's
  stored output can disagree with its own code.
- **`make_test_system.py` corrected.** As supplied it stripped hydrogens,
  against the recipe in §6. Meeko requires them.
- **Vina on Windows** is the official 1.2.7 binary, because `pip install vina`
  needs Boost and PyPI ships no Windows wheel.
- **Python is 3.12.10**, not the book's 3.12.3. **Open Babel is 3.1.0**, not
  3.2.1 — checked against ch04's values, which are unchanged.
- **Disordered side chains are typed down to alanine**, not deleted, wherever
  the remaining atoms are exactly alanine's. Anything else stops the run.
- **`ch05` and `ch20` gained tests** not listed in the plan, because both have
  explicitly named expected values.

---

## What a reader should know before trusting a number here

1. **The three-decimal values are Linux values.** Windows agrees to about two.
2. **The RMSD values in ch17 were measured on Windows** and the scores
   underneath them are build-dependent, so a pose ranking can flip — 4JXS's
   correct pose sits at mode 3, 0.09 kcal/mol below mode 2.
3. **Two chapters disagree with the book** and both numbers are printed side by
   side in the chapter, in `PROGRESS.md`, and above.
4. **Nothing here was tuned to match.** Where a value did not reproduce, the
   cause was investigated and reported; where it could not be resolved, both
   numbers stand.
