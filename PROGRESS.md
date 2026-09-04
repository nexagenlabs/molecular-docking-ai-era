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
- [x] 2.2 `ch08_ligand_prep` — exact on Linux; the book's counts are from the deprotonated form (Phase 5)
- [x] 2.3 `ch04_formats` — all four formats behave exactly as §6 describes
- [x] 2.4 `ch17_validation` — 1.114 / 2.999 / 10.526 Å; 6 tests pass
- [x] 2.5 `ch18_enrichment` — all eight published values reproduce exactly once the construction was supplied (Phase 5)
- [x] 2.6 `ch10_flexibility` — exactly Gln120, Leu293, Thr316; eight residues ≤20°
- [x] 2.7 `ch21_molecular_dynamics` — all eleven published values reproduce exactly once the construction was supplied (Phase 5)

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

- [x] 4.1 root README — written last, with the chapter table
- [x] 4.2 cross-checks — 25/25 directories, run.sh strict, no --minimize, no
      unset seed, no TODO(value), every chapter run end to end from clean
- [x] 4.3 `BUILD_REPORT.md`

**Gate 4: report delivered.** 75 passed, 15 xfailed, 0 failed.

## Phase 5 — the three open items closed

Two book defects were found by this build and have been fixed in the book; two
constructions that `CLAUDE.md` had recorded only by their results were supplied.

- [x] 5.1 `ch08_ligand_prep` — **book defect, fixed.** The published counts came
      from the neutral forms while the chapter's own workflow says protonate
      first. The deprotonated counts are now the authoritative ones:
      STC 15/15/16/16/16, 18U 9/9/12/11/8, 1MU 33/35/33/28/37. Script, README,
      expected results and test updated; the neutral column is kept alongside,
      because a conformer table that does not say which form it used cannot be
      reproduced.
- [x] 5.2 `ch18_enrichment` — construction supplied as
      `scripts/ch18_make_screens.py`, wired into `run.sh`, imported by
      `enrichment.py` so there is one definition of the screens. **8 of 8
      published values reproduce exactly.**
- [x] 5.3 `ch21_molecular_dynamics` — construction supplied as
      `scripts/ch21_make_trajectory.py`, same treatment. **11 of 11 published
      values reproduce exactly**, negative slopes included.
- [x] 5.4 `ch17_validation` — the book's `[x]` placeholders now carry this
      build's 1.114 / 2.999 / 10.526 Å, with the mode-3 finding and the 5.9 Å
      chain sensitivity. Chapter text updated to match; no values changed.
- [x] 5.5 `tests/conftest.py` — `unknown_construction()` removed. No chapter
      needs it any more.
- [x] 5.6 full suite rerun; ch08, ch17, ch18 and ch21 also re-run through their
      own `run.sh` from a clean state. ch17 reproduced 1.114 / 2.999 / 10.526 Å
      and the 4.609 Å chain-B check unchanged.

- [x] 5.7 `require_platform()` replaced by a non-strict `@platform_xfail`
      marker. The imperative `pytest.xfail()` aborted the test before its
      assertion, so a value matching off Linux was never checked — which is how
      ch08's STC row went on being reported as platform-dependent after it had
      started matching the book exactly on Windows. It now reports XPASS.

**Gate 5: 94 passed, 3 xfailed, 1 xpassed, 0 failed.** The xfails are the known
Windows-only exact-value tests: ch08's 18U and 1MU conformer rows and ch09's box
scores. The xpass is ch08's STC row, which matches the book on Windows too.
Eleven of the previous fifteen xfails were the two missing constructions;
nothing from ch18 or ch21 xfails now.

---

## Closed

### ch08's conformer counts came from the wrong protonation state

**Status: closed. A real defect in the book, now corrected.**

`CLAUDE.md` originally gave the ETKDGv3 settings without saying which
protonation state was embedded, and its counts (17/16/15/16/15 for STC) matched
neither platform when the charged forms were used. Embedding the neutral form
reproduced them exactly on Linux, so this build recorded the book as right and
the protocol as under-specified.

That was the wrong conclusion, and the right one was reachable: the chapter's
own workflow protonates before generating conformers, so the published counts
had been produced in the opposite order to the procedure printed beside them.
The counts are now the deprotonated ones — STC 15/15/16/16/16,
18U 9/9/12/11/8, 1MU 33/35/33/28/37 — and this repository's earlier "docked
form, for comparison" column turns out to have been the authoritative one all
along.

**What to take from it:** an expected value that reproduces is evidence, not
proof. Both orderings produce a table; only one of them matches the procedure.
Agreement with a published number can confirm a mistake as readily as a result
when the number and the procedure were never checked against each other.

On Windows the deprotonated counts give the STC row exactly and differ by one
to three elsewhere (18U 9/9/**11**/11/8, 1MU 33/35/33/**29**/**34**) — the same
build-level difference as ch09.

### ch18's screen construction

**Status: closed. The construction was supplied; everything reproduces.**

`ch18_make_screens.py` searches `hi` over 40–69 and `lo` over 2000–6900 for the
pair of screens with the closest AUCs, and lands on hi = 56, lo = 4800 with the
two AUCs 1.6×10⁻⁴ apart. The single generator is consumed sequentially across
the whole nested search, so the loop bounds and their order are part of the
specification — which is why it was not guessable from the results, and why the
file is imported rather than copied.

All eight published values reproduce exactly: AUC 0.758 for both screens, EF1%
56.0 and 0.0, EF5% 11.6 and 0.6, BEDROC 0.574 and 0.058. BEDROC still agrees
with `rdkit.ML.Scoring.Scoring.CalcBEDROC` to six decimals, and the 79.8% weight
figure is analytic as before.

The earlier reconstruction reached 45.0 / 11.0 / 0.555 for screen A. It was not
adjusted toward the book, and that was the right call: the gap was a missing
recipe, exactly as recorded, and no amount of parameter fitting would have
turned into the real one.

### ch21's noise realisation

**Status: closed. The construction was supplied; everything reproduces.**

The trajectory is four **Ornstein-Uhlenbeck** relaxations at τ = 0.04, 1.2, 30
and 700 ns, amplitudes 0.50/0.55/0.65/0.90, seed 2101, 3000 ns at 0.01 ns —
`ch21_make_trajectory.py`. The generator is consumed once per process in the
order of `taus`.

The argument this build made from the numbers alone was correct as far as it
went: **a monotone sum of exponentials cannot produce a negative slope**, so the
book's −0.150 and −0.010 had to come from a stochastic term. What was missing
was that the stochastic term is not additive measurement noise sitting on top of
the exponentials — each relaxation *is* an OU process. `CLAUDE.md` omitted it.

All eleven published values reproduce exactly: four means, four second-half
slopes, three values at ten times the window. All four windows pass the
flat-tail test, two of them with a falling tail.

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

## The three RMSD values now printed in Chapter 17

Mode 1, symmetry-corrected, heavy atoms, no superposition, seed 42,
exhaustiveness 32, on Windows:

| Entry | Ligand | Affinity | **RMSD** | Best over 9 modes |
|---|---|---|---|---|
| 1L2S | STC | −7.377 | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | −7.805 | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | −8.131 | **10.526 Å** | 10.371 Å (mode 4) |

One pass, one near-miss ranked third, one failure. The best affinity is
inversely ordered against the RMSD — 4JXV scores best and is wrong by 10 Å.
These filled the chapter's `[x]` placeholders, along with the mode-3 finding and
the chain sensitivity below.

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
