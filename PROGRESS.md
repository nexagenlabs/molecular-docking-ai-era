# PROGRESS

Session memory for the autonomous build. Updated after every completed task.

## Phase 0 — foundation

- [x] directory skeleton (25 chapter directories, stub READMEs, outputs/expected)
- [x] `.gitignore`, `.gitattributes`
- [x] `LICENSE` — MIT, Suryaprakash Tripathy
- [x] `errata.md`
- [x] `README.md` placeholder (rewritten properly in Phase 4)
- [x] `PROGRESS.md`
- [x] `environment/environment.yml`, `requirements.txt`, `environment/README.md`
- [x] environment created and `environment/resolved.txt` written
- [x] `data/structures/fetch.sh` — run, checksums recorded
- [x] `data/ligands/` — SDFs generated and committed, `generate.py --check` passes
- [x] `scripts/audit_structures.py` — every structural claim re-measured
- [x] `protocols/reproducibility_record.md` — Chapter 20's seventeen fields
- [x] `tests/` — pytest harness, 67 tests, collection clean

## Phase 1 — the pattern chapter

- [x] `ch09_first_run` — AmpC run, four demonstrations, gate accepted
- [x] `ch09_first_run` — synthetic system, config, plan-named scripts
- [x] Gate 1 — `pytest tests/test_ch09_first_run.py` passes (1 xfail: the exact
      box scores, which are Linux-only and diagnosed below)

## Phase 2 — chapters with hard expected values

- [x] 2.1 `ch05_receptor_prep` — 15 tests pass; every §2.1 value reproduces
- [x] 2.2 `ch08_ligand_prep` — exact on Linux once the neutral form was identified
- [x] 2.3 `ch04_formats` — all four formats behave exactly as §6 describes
- [x] 2.4 `ch17_validation` — 1.114 / 2.999 / 10.526 Å; 6 tests pass
- [x] 2.5 `ch18_enrichment` — AUC, RDKit cross-check and the 79.8% weight all reproduce; EF/BEDROC differ, see Blocked
- [x] 2.6 `ch10_flexibility` — exactly Gln120, Leu293, Thr316; eight residues ≤20°
- [x] 2.7 `ch21_molecular_dynamics` — means within 0.1 Å, shortfall 38% vs 37%; slopes blocked, see below

## Phase 3 — remaining chapters

- [x] `ch26_case_study` — 3x3 cross-dock, redock 1.114 Å, series too tight to rank
- [x] `ch06_predicted_structures` — 0.216 Å backbone, 3.140 Å pose
- [x] `ch07_pocket` — four box definitions, all within 0.09 Å
- [x] `ch20_protocol_record` — blank, filler, worked AmpC example; 7 tests
- [x] `ch02_method_choice` — synthesis; every row read from another chapter's output
- [x] `ch03_databases` — API and file header agree on all four entries
- [x] `ch11_web_servers` — upload set + audit: 9 of 17 fields recordable, 3 tier-one lost
- [x] `ch12_screening` — 19 compounds, one preparation failure, cost measured
- [x] `ch13_cofolding` — input written and frame-checked; boltz attempted, breaks the env
- [x] `ch14_boltz2` — r² = 0.38 against FEP+ 0.52; pairwise ranking simulated and checked analytically
- [x] `ch15_cofolding_field` — the r-versus-R² comparison, in both directions
- [x] `ch16_rescoring` — arithmetic runs; GNINA attempted and documented as unavailable
- [x] `ch22_free_energy` — needs σ < 0.116; best available is 0.20
- [x] `ch23_interactions` — 93% of interactions recovered at 1.114 Å
- [x] `ch24_network_pharmacology` — refuses without a background, exit 2
- [x] `ch25_hit_to_bench` — assay design covers all three measured Ki
- [x] `ch27_methods` — methods text generated from the record, gaps left visible

## Phase 4 — integration

- [ ] 4.1 root README
- [ ] 4.2 cross-checks
- [ ] 4.3 BUILD_REPORT.md

---

## Blocked / needs a decision

### Three-decimal values do not reproduce on Windows

**Status: diagnosed, not blocking. The book is right; the platform is the
variable.**

Chapter 9's synthetic box sweep, same Vina 1.2.7, meeko 0.8.0, RDKit 2026.3.5:

| Where | 20 Å | 12 Å | 8 Å |
|---|---|---|---|
| Book | −4.905 | −4.911 | −2.748 |
| Native Linux (WSL, this machine) | **−4.905** | **−4.911** | **−2.748** |
| Native Windows | −4.910 | −4.903 | −2.686 |
| Linux Vina, Windows-built ligand | −4.904 | −4.896 | −2.728 |

Two independent causes, both measured:

1. **The RDKit build.** Windows and Linux RDKit 2026.3.5 give different MMFF
   optimised coordinates from the same `EmbedMolecule(randomSeed=11)`. The
   receptor, built with numpy's PCG64, is byte-identical across the two — so
   the divergence is the force field's convergence, not the RNG.
2. **The Vina build.** Handed the identical Windows-built ligand and receptor,
   Linux and Windows Vina return different scores (−4.904 vs −4.910 at 20 Å).

**Consequence for the repository:** seed 42 gives byte-identical results within
a build, not across builds, and nothing in the log distinguishes the two
situations. Exact-value tests assert three decimals on Linux and behaviour
elsewhere. `scripts/docking_common.py` carries the measurements and
`is_reference_platform()`.

### ch08's conformer counts are from the NEUTRAL form

**Status: resolved. The book is right; the protocol was under-specified.**

`CLAUDE.md` §6 gives the ETKDGv3 settings but not which protonation state is
embedded. Docking the charged forms gave 15/15/16/16/16 for STC against the
book's 17/16/15/16/15 — close, but wrong on both platforms, so it was not the
build. Embedding the **neutral** (drawn) form reproduces all three rows exactly
on Linux: 17/16/15/16/15, 10/14/9/9/9, 33/39/33/30/40.

So the order of operations is: generate conformers on the drawn molecule, apply
protonation when writing the ligand for docking. The chapter now prints both
columns, because a conformer table that does not say which form it used cannot
be reproduced.

On Windows the neutral counts are 16/16/15/16/15 for STC and off by one or two
elsewhere — the same build-level difference as ch09.

### ch18's screen construction is not recorded, so EF and BEDROC differ

**Status: blocked on information, not on work. Both numbers recorded; neither
adjusted.**

`CLAUDE.md` §6 gives the book's results for the two synthetic screens but not
the construction that produced them. Everything downstream of AUC depends on
exactly how the actives are arranged, and many arrangements give AUC 0.758.

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 45.0 | 11.0 | 0.555 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.8 | 0.059 |

What does reproduce, and is checkable independently of the construction:

- **Both screens land on AUC 0.758**, by solving for the active score mean.
- **BEDROC agrees with `rdkit.ML.Scoring.Scoring.CalcBEDROC` to six decimals**,
  from an implementation written directly from Truchon & Bayly (2007).
- **79.8% of the α=20 weight falls in the top 8%** — analytic, exact.
- Screen B finds nothing in the top 1% while Screen A finds 45 of 100.

A rank-based construction was also tried (56 actives spread through the top
90 ranks, two more by rank 500, the remainder in a solved block): AUC 0.7574,
BEDROC 0.5752 against the book's 0.574. Closer, and still not exact. Both
routes get near the book without landing on it, which is what one would expect
when the recipe rather than the arithmetic is what is missing.

**Not pursued further on purpose.** Fitting free parameters until the four
published numbers appear would produce a script that agrees with the book by
construction rather than by measurement.

### ch21's noise realisation is not recorded, so the slopes differ

**Status: blocked on information. The deterministic half is recovered; the
stochastic half cannot be.**

`CLAUDE.md` §6 says the trajectory has four separated relaxation timescales and
gives the resulting statistics, but not the amplitudes, the noise or the seed.

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | −0.150 | +0.113 |
| 10 ns | 1.47 Å | 1.42 Å | −0.010 | +0.015 |
| 100 ns | 1.90 Å | 1.80 Å | +0.007 | +0.004 |
| 1000 ns | 2.34 Å | 2.30 Å | +0.0004 | +0.0000 |

The decisive observation: **a monotone sum of exponentials cannot produce a
negative slope at all.** The book's two negative slopes must come from noise, so
they are a property of one realisation. Fitting amplitudes and timescales
jointly to all seven published numbers leaves a residual of about 0.08 Å that
will not reduce — the size a noise realisation would explain.

What reproduces: the means to within 0.1 Å, the ordering, every window from
10 ns up passing the flat-tail test, and the chapter's actual claim — the 10 ns
answer is 38% below the 1000 ns one against the book's 37%.

### Open Babel is 3.1.0, not the pinned 3.2.1

`openbabel-wheel` ships a cp312 Windows wheel built from Open Babel 3.1.0; no
3.2.1 Windows wheel exists. ch04's round-trip results are Open Babel's output,
so this could move a published value. **Run and compared: it did not.** PDB and
MOL2 preserve charge, bond orders and stereochemistry; PDBQT returns the
dianion neutral with the atom order changed; XYZ loses charge. Every §6 claim
for this chapter holds on 3.1.0.

## The environment was broken once, and repaired

**`pip install boltz` (ch13) silently downgraded the pinned environment.**

It succeeds on a CPU-only machine and pulls numpy down to 1.26.4, gemmi to
0.6.5 and scipy to 1.13.1 — the three pins that ch08's conformer counts, ch17's
RMSD and meeko's PDBQT output all depend on. No error; pip simply resolved its
own constraints.

Repaired immediately: boltz and its eighteen leftover dependencies uninstalled,
`numpy==2.4.4 gemmi==0.7.5 scipy>=1.17.1 rdkit==2026.3.5 meeko==0.8.0
spyrmsd==0.9.0` reinstalled, versions verified, and the **full test suite
re-run and passing** before any further work. `environment/resolved.txt` should
be regenerated before release.

The finding is recorded in ch13's README as a reproducible property of that
package rather than as general advice: **install co-folding models in a
separate environment.**

## Software that could not run here

- **GNINA** (ch16) — compiled binary, CUDA dependency, no PyPI/conda-forge
  package and no Windows build. `pip install gnina` attempted: no distribution.
  The pipeline is written, attempted once, and exits 3 with the exact command
  it would run. Nothing simulated.
- **Boltz-2** (ch13) — installs, but needs a CUDA GPU and several GB of
  weights, and breaks the pinned environment on the way in (above). The input
  YAML is written and frame-checked against the crystal structure regardless,
  since it is the half a reader can check without a GPU.
- **PDBFixer** (ch05) — conda-forge only, pulls in OpenMM. Documented in ch05's
  README as the alternative to typing disordered side chains down to alanine;
  not installed, and the code shown there is not run.

## Deviations from CLAUDE.md

- **Notebooks are scripts.** `CLAUDE.md` §6 calls for a notebook in ch14 and
  ch18. Both are Python scripts that write a Markdown report and a PNG instead.
  A script runs in CI and fails loudly; a notebook has to be executed by hand
  and its stored output can disagree with its code. The substance the book asks
  for is present in both cases — ch14 prints the squaring step, ch18 plots both
  screens on one axis.

- **`make_test_system.py` wrote the ligand without hydrogens.** The file as
  supplied called `Chem.MolToMolFile(Chem.RemoveHs(m), "lig.sdf")`, but the
  recipe in `CLAUDE.md` §6 says `Chem.MolToMolFile(m, "lig.sdf")` with the
  comment "explicit Hs — meeko requires them". Meeko does require them: on the
  stripped file it writes no PDBQT and reports an error. Corrected to match the
  recipe, which then reproduces the book's numbers exactly on Linux.
- **`make_test_system.py` location.** `CLAUDE.md` §6 says
  `scripts/make_test_system.py`; `SESSION_PLAN.md` §1.2 says it belongs to
  ch09. It lives at `ch09_first_run/scripts/make_test_system.py`.
- **Vina on Windows** is the official `vina_1.2.7_win.exe` binary, because
  `pip install vina==1.2.7` needs Boost and PyPI ships no Windows wheel. Same
  upstream release, driven through the same command line.
- **Python is 3.12.10**, not the book's 3.12.3.
- **Ten disordered chain B side chains are typed as alanine** in ch09's AmpC
  receptor rather than deleted. REMARK 470 says they are missing their distal
  atoms, so the file holds exactly alanine's heavy atoms; deleting the residues
  would remove backbone, and Lys290's centre of mass is 1.1 Å outside the 20 Å
  box face. Chapter 5 describes rebuilding with PDBFixer as the alternative.

## The three RMSD values for Chapter 17's placeholders

Mode 1, symmetry-corrected, heavy atoms, no superposition, seed 42,
exhaustiveness 32, on Windows:

| Entry | Ligand | Affinity | **RMSD** | Best over 9 modes |
|---|---|---|---|---|
| 1L2S | STC | −7.377 | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | −7.805 | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | −8.131 | **10.526 Å** | 10.371 Å (mode 4) |

One pass, one near-miss ranked third, one failure. The best affinity is
inversely ordered against the RMSD — 4JXV scores best and is wrong by 10 Å.

**4JXV chain sensitivity:** chain A gives 10.526 Å, chain B gives 4.609 Å. The
chain was chosen because it needed one altloc decision instead of two, which
sounds cosmetic and moves the answer by 5.9 Å.

## Timings for the book's hardware note

Chapter 9, AmpC system, 4 cores, Windows 11, seed 42:

| Exhaustiveness | Wall time |
|---|---|
| 8 | 6.8–7.3 s |
| 32 | 27.0 s |

Ratio 3.7, inside the 3–5 band. The book's 3.4 s and 14.2 s were a different
machine and a much smaller ligand — the synthetic system, not AmpC.
