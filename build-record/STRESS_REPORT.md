# Stress report

Results of `STRESS_TEST.md`, run against commit `79e26b8` on Windows 11,
Python 3.12.10.

**All seven checks were attempted. Nothing was fixed** *during the testing
session this report describes.* Every mutation was reverted before the next;
the clone and the working repository both end clean. Total elapsed: 30 minutes
of the two-hour budget.

**Twelve of the thirteen findings were fixed afterwards, in commits `c3fda90`
through `685f3b1` and after. One remains open (B4), and B5 is a decision
rather than a repair.** See **Resolution** at the end. Nothing
between here and there has been edited: B1–B13 read as they did at `79e26b8`,
because a report rewritten to describe the repaired code would no longer be
evidence that the clean-clone test caught anything.

All work happened in a throwaway clone at
`…/scratchpad/clonetest`, provisioned as `environment/README.md` instructs and
run with `PATH` scrubbed of the parent repository's `.venv/Scripts`. Without
that scrub the clone silently borrowed the working repository's `obabel` and
would have passed for the wrong reason.

---

## Summary

| Check | Result |
|---|---|
| 1. Clean-clone test | **FAILED** — 4 findings, 1 a genuine defect (F4) |
| 2. Mutation testing | **5 of 7 caught**; 2 holes, 3 further weaknesses |
| 3. Adversarial inputs | **4 of 6 clean**; 2 failures |
| 4. Book-to-code, reversed | 54 of 62 §6 values asserted; 6 genuinely uncovered |
| 5. Documentation honesty | **PASSED** — 0 discrepancies; 2 side findings |
| 6. xfail audit | **PASSED** — all four reasons true; 1 over-claim exposed |
| 7. Fresh-eyes read | **Adapted** — subjective half skipped by design, see below |

**Headline.** The repository reproduces from a clean clone: 92 of 98 tests pass
with no tools and 25 of 25 chapters run end to end from a foreign working
directory. What it does not do is detect certain classes of its own breakage,
and one pair of tests passes only because of leftover state.

### A distinction the rest of this report keeps

- **The three-decimal values were produced and verified on Linux, Python 3.12.3
  on Ubuntu.** That is not in question here and nothing below disputes it.
- **What has never been verified on Linux is the documented install path** —
  `pip install -r requirements.txt` followed by `pytest`. This machine cannot
  test it: WSL here is Ubuntu 22.04 / Python 3.10.12 with no `ensurepip` and no
  Open Babel.

---

## The bug list

Classified as asked: defect in code, gap in documentation, environment problem,
or disagreement with the book. **No disagreement with the book was found.**

### Defects in code

**B1 — ch20's tests assert a state the suite never builds.** *(F4, check 1)*
`tests/test_ch20_protocol_record.py` runs `fill_record.py` with defaults, which
reads `ch09_first_run/outputs/ampc/logs/modes.log`. That log is produced only by
the **AmpC branch of `ch09_first_run/run.sh`**, is exercised by no test, and is
gitignored. In a fully provisioned clean clone the record carries five TODOs
instead of three, `tier_one_complete` is `False`, and two tests fail.

Proved end to end: after running `ch09_first_run/run.sh` in the clone, **all
seven ch20 tests pass.** The dependency is real, silent, and undeclared.

**B2 — the good error message guards the wrong file.** *(the secondary half of
F4, and the one worth acting on first)*
`fill_record.py` is asymmetric about its two inputs:

```python
if not config_path.exists():
    sys.exit("%s missing -- run ch09_first_run/run.sh first" % config_path)
log = read_log(log_path) if log_path.exists() else {}      # silent
```

A missing **config** stops the run with exactly the right sentence. A missing
**log** degrades silently to `None`, which is what lets B1 exist at all. The
sentence that would have prevented the defect is already written — it is
attached to the input that was never going to be missing.

This is the only chapter in the repository that degrades silently on a missing
upstream artefact. **ch02 and ch23 both get it right**, and were tested:

- ch02, run first with five upstream chapters unrun, named every missing file,
  marked each row `NOT MEASURED`, counted them, and printed *"These are gaps,
  not defaults. Run the chapter."*
- ch23, with ch17's outputs moved aside, exited 1 with
  `…1L2S_STC_ref.sdf missing -- run ch17_validation/run.sh first`.

The correct pattern is already in the codebase twice. ch20 does not follow it.

**B3 — unguarded SDF reads traceback on bad input.** *(check 3)*
An empty `data/ligands/STC.sdf` makes `ch04_formats/scripts/roundtrip.py` die
with a raw `OSError` traceback from `Chem.SDMolSupplier`, not a message. The
pattern `next(Chem.SDMolSupplier(...))` appears unguarded at **eight call
sites**: ch03, ch04 (×2), ch06, ch07, ch08, ch12, ch17. Every other adversarial
input in the repository fails cleanly; this class does not.

**B4 — `ch09/run.sh` dirties a tracked file.** *(check 5)*
Running the chapter regenerates `ch09_first_run/config/vina_config.txt`, whose
only diff is its embedded generation timestamp:

```
-# Written by scripts/derive_box.py on 2026-09-04 08:11 UTC.
+# Written by scripts/derive_box.py on 2026-09-04 11:33 UTC.
```

Every number is identical, which is the good news. But it is the only tracked
file that running all 25 chapters modifies, and it leaves `git status` unable to
distinguish "I edited something" from "I ran the chapter".

### Gaps in the test suite

**B5 — the ch08 conformer mutation is invisible on Windows.** *(check 2, M2)*
Generating conformers from the neutral form instead of the deprotonated one — a
mutation that reverses the very defect fixed in the last session — produces
**zero failures** on Windows. The non-strict xfail absorbs it: STC merely flips
from XPASS to XFAIL and the suite stays green.

Confirmed to be platform-conditional, not universal: with the gate forced on
(`on_reference_platform()` → `True`, reverted immediately), all three conformer
tests fail loudly with `assert [16, 16, 15, 16, 15] == [15, 15, 16, 16, 16]`.
So the mutation **is** caught on Linux and invisible off it.

This is the cost of the non-strict marker, not an argument against it — the same
mechanism is what exposed the STC over-claim in check 6. It is worth knowing
that a Windows-only run cannot police ch08's protonation order.

**B6 — ch24's refusal is asserted by nothing.** *(check 2, M6)*
There is no `tests/test_ch24*` file at all. The behaviour itself is correct and
was verified by hand: with no `--background` the script exits **2** with
`REFUSING TO RUN: no background gene list given.`; with `--background genome` it
runs and reports fold 20.83. But nothing would notice if the refusal were
removed. More broadly, **only 9 of the 25 chapters have a test file** (ch04,
ch05, ch08, ch09, ch10, ch17, ch18, ch20, ch21).

**B7 — three tests are weaker than their names promise.** *(check 2)*

- `test_no_vina_config_leaves_the_seed_unset` accepts `seed = 0` — the one value
  that means "choose at random", i.e. exactly the condition the test exists to
  prevent. Its regex asks whether a seed is *present*, not whether it is usable.
- `test_the_rmsd_call_passes_minimize_false_explicitly` passed while
  `validate.py` was actually calling `minimize=True`, because it substring-
  matches `minimize=False` anywhere in the file — including the prose that
  explains the trap. The mutation was caught, but by the *other* guard.
- `test_the_ligand_copy_was_chosen_by_distance` did **not** catch selection by
  file order. Replacing the distance search with `copies[0]` picked A/1115,
  which is also 2.70 Å from Ser64 OG, so the distance assertion held. The
  mutation was caught by `test_the_worked_example_matches_the_book` on copy
  identity instead — the wrong chain, A, which is the one missing Lys290–Ala292.

### Gaps in documentation

**B8 — `pip install -r requirements.txt` cannot succeed on Windows.**
`vina==1.2.7` publishes manylinux and musllinux wheels for cp38–cp312 and
nothing else; Windows falls back to the sdist, which needs Boost. pip fails
during resolution so **nothing at all installs**. `environment/README.md` says
"Everything else installs from `requirements.txt` on Windows Python 3.12" — that
is false as written. Deleting the one `vina` line makes the rest install
cleanly; verified. Not a defect on the reference platform, where the wheel
exists.

**B9 — `pytest` is not in `requirements.txt`.** Platform-independent. The root
README says to run `pytest`; after a clean documented install it does not exist
(`No module named pytest`). The suite is the repository's main evidence and the
documented install does not provide the means to run it.

**B10 — Open Babel on Windows is undocumented and misdescribed.**
`requirements.txt` says "NOT installable from pip: Open Babel 3.2.1, a system
binary." The author's own working environment contains `openbabel-wheel==3.1.1.23`,
a pip package, and that is what makes ch04 run on this machine.

**B11 — ten undeclared cross-chapter dependencies.** *(check 7)*
Scripts that read another chapter's `outputs/` or `config/` without their README
naming that chapter: **ch02** (reads ch06, ch10, ch12, ch14, ch16, ch17, ch22,
ch26), **ch16** (ch17), **ch23** (ch17). Only ch20 and ch27 declare theirs. Low
severity because ch02 and ch23 announce the dependency at runtime — but B1 shows
what happens in the one case where a script does not.

**B12 — a disjoint box returns `0.0` and no warning.** *(check 3)*
Driving the repository's own `dock()` helper with the synthetic system and a box
centred 100 Å away returns **affinity 0.0, exit 0**. The undersized-box trap is
documented prominently; the disjoint-box case is not, and `0.0` is not obviously
wrong the way a negative number is. ch09's `test_box_sweep_raises_no_error`
already asserts `score < 0`, so the repository knows the shape of this check —
it just is not applied anywhere a reader would run.

**B13 — ch13 and ch16 exit 0 while reporting they cannot run.**
Both `run.sh` wrap the refusal in `|| true`, so the chapter exits 0 although the
underlying script exits 3. The prose is honest — the logs say plainly *"gnina is
not installed, so this pipeline cannot run here"* — but a machine reading exit
codes cannot tell a full run from a skipped one.

### Environment problems

None beyond B8, which is a documentation gap about a real platform constraint.

### Disagreements with the book

**None found.** Check 4 located no §6 value that the code contradicts.

---

## Check-by-check detail

### Check 1 — clean-clone test: FAILED

Two runs, both with `PATH` scrubbed:

| | Run A (no external tools) | Run B (provisioned) |
|---|---|---|
| Passed | 68 | **92** |
| Failed | 6 | **2** |
| Errors | 20 | 0 |
| xfailed / xpassed | 3 / 1 | 3 / 1 |
| Wall time | 102 s | 233 s |

**Passes worth recording.** All 176 tracked files clone; nothing a script needs
is absent from version control. `data/structures/fetch.sh` works and all four
SHA-256 sums match `data/structures/README.md` exactly. In run A the 26
tool-absence failures produce **zero tracebacks** — every one names the tool and
points at `environment/README.md`.

**Failures.** B8, B9, B10 at the install step; B1/B2 in run B.

### Check 2 — mutation testing: 5 of 7 caught

| Mutation | Predicted detector | Actual result |
|---|---|---|
| ch09 config `seed = 42` → `0` | reproducibility test | **caught** — but by `test_seed_is_cross_checked_between_config_and_log` (`'0' == '42'`). The reproducibility test never reads the config; it uses `verify_run.py`'s hard-coded seeds. |
| ch08 conformers on the neutral form | conformer count test | **NOT caught on Windows** (B5); caught on Linux, confirmed by forcing the gate |
| ch17 RMSD `minimize=True` | gotcha test + RMSD values | **caught** statically by `test_no_script_uses_minimize`, before any docking. Second guard fooled (B7) |
| select the first HETATM group | ligand-copy test | **caught**, by copy identity not by distance (B7). *Re-scoped:* ch05 reports all three copies rather than selecting, so the mutation has no target there; applied to ch20's `fill_record.py`, where selection happens |
| ch18 re-seed inside the search loop | AUC, EF, BEDROC | **caught** emphatically — 10 failures including the construction's own `assert 40 == 56` |
| ch24 whole-genome background | refusal test | **NOT caught** — no such test exists (B6) |
| skip deprotonation in `generate.py` | charge assertion | **caught** by the script's own hard failure: `STC: formal charge is +0, the series table says -1. Stop -- do not dock this.` |

### Check 3 — adversarial inputs: 4 of 6 clean

| Input | Result |
|---|---|
| Nonexistent entry `9ZZZ` | **pass** — exit 1, `…9ZZZ.pdb missing -- run: bash data/structures/fetch.sh` |
| Structure with no ligand (1L2S stripped of HETATM) | **pass** — `No ligand-like HETATM group found`, exit 0, correct for a QC report. ch17, which must have a ligand, refuses: `sys.exit("%s: no catalytic %s copy in chain %s")` |
| Unparseable SMILES `C1CC` | **pass** — exit 1, `STC: SMILES did not parse` |
| Empty SDF | **FAIL** — raw `OSError` traceback (B3) |
| Box not overlapping the ligand | **FAIL** — affinity `0.0`, exit 0, no warning (B12) |
| `run.sh` from another working directory | **pass** — all 25 use `cd "$(dirname "$0")/.."`; five verified from `/`, all exit 0 |

### Check 4 — book-to-code agreement, reversed

Of 62 distinct numeric literals in `CLAUDE.md` §6 (structural noise removed),
**54 appear somewhere in `tests/`, 8 do not**. The method counts a value as
covered if it appears anywhere in the suite, even in a comment, so the eight are
uncovered for certain.

| Value | Where it lives | Verdict |
|---|---|---|
| 3.4, 14.2 | ch09 timings | **correctly uncovered** — §6 says "absolute times are hardware-specific; assert only that the ratio is 3–5", and the ratio *is* asserted |
| 140, 10.5, 1.5 | synthetic receptor recipe | named constants in `make_test_system.py` (`SHELL_ATOMS = 140`, `SHELL_MIN, SHELL_SPAN = 9.0, 1.5`), asserted nowhere |
| 0.38 | ch14 r² | computed and printed; the chapter states it is "shown rather than asserted"; no test file |
| 0.90 | ch16 Vina EF1% | a value in a dict, printed; no test file |
| 1.75 | ch26 published redock | `PUBLISHED_REDOCK_RMSD = [1.75, 1.87]`; no test file |

So six values are genuinely unchecked, and all six sit in chapters with no test
file (B6).

### Check 5 — documentation honesty: PASSED

All 25 chapters were run end to end from a foreign working directory. **Every
one exits 0.**

- **Output paths:** every `outputs/…` path named in a README exists after its
  chapter runs. Two apparent misses were artefacts of my own regex — ch05's
  `outputs/qc_<PDBID>.md` is a placeholder whose real files exist, and ch27's two
  paths are *other* chapters' outputs written with full prefixes.
- **Commands:** every `bash`/`python` command shown in a README names a file
  that exists. Zero exceptions.
- **Chapters that cannot run here:** ch13, ch16 and ch05's PDBFixer section all
  say so plainly in prose. The only gap is the exit code (B13).

Side findings: B4 and B13.

### Check 6 — xfail audit: PASSED

| Test | Marked | Reason still true? |
|---|---|---|
| ch08 `[STC]` | **XPASS** | **No — and that is the point.** Windows reproduces `15, 15, 16, 16, 16` exactly. The marker's reason over-claims for this row, and the non-strict marker is what surfaced it. |
| ch08 `[18U]` | XFAIL | Yes — differs at seed 42 only (11 vs book 12) |
| ch08 `[1MU]` | XFAIL | Yes — differs at seeds 99 (29 vs 28) and 2026 (34 vs 37) |
| ch09 box scores | XFAIL | Yes — −4.910 / −4.903 / −2.686 against −4.905 / −4.911 / −2.748, matching the values already recorded in `BUILD_REPORT.md` |

Twelve of ch08's fifteen counts match on Windows and three differ, exactly as
`CLAUDE.md` §6 now states.

**Is any xfail masking a real defect?** Not by way of a false reason — every
reason checks out, and the deltas are stable and match what was recorded
previously. But the *mechanism* suppresses failure regardless of cause, which is
B5: on Windows these tests cannot distinguish a platform difference from a code
change. The behavioural claims around them (box 8 worse than 20 and 12, 20 ≈ 12,
charges, rotatable bonds) are asserted separately and pass on both platforms, so
the exposure is limited to the exact values.

**Would they pass on Linux?** Not re-confirmed here, and not claimed. The values
were produced and verified on Ubuntu / Python 3.12.3; this machine has no Linux
environment capable of repeating that.

### Check 7 — fresh-eyes read: adapted

**The subjective half was skipped deliberately**, per your note: I wrote much of
this code and cannot give it fresh eyes. Reporting an impression of my own prose
would be worth nothing.

The objective half was run instead, because F4 is an instance of a general
shape: **which chapters read another chapter's generated output without saying
so?** Result is B11 — ten undeclared dependencies across ch02, ch16 and ch23 —
together with the finding that ch02 and ch23 handle the missing-input case
correctly at runtime, which is what makes ch20's silence (B1, B2) stand out as a
defect rather than a house style.

---

## Resolution

Everything above is the report as written at `79e26b8` and is unchanged. This
section is what happened next.

### The three weak tests, re-tested by mutation

B7 is the finding that mattered most, because a test that reports protection it
is not providing is worse than no test: it stops anyone looking. So the fix is
recorded the way the defect was found — by breaking the code and watching,
rather than by reading the new tests and judging them adequate.

Each mutation was applied to the repaired tree, run against
`tests/test_gotchas.py`, `tests/test_ch09_first_run.py`,
`tests/test_ch17_validation.py` and `tests/test_ch20_protocol_record.py`, then
reverted. Those four files are part of the default `pytest` run, so a failure
in any of them is a red suite. The tree was confirmed clean and green after all
three reverts.

| Mutation | At `79e26b8` | Now |
|---|---|---|
| `minimize=False` → `minimize=True` in `ch17_validation/scripts/validate.py` | caught by **1** of the 2 intended guards. `test_the_rmsd_call_passes_minimize_false_explicitly` **passed**, because it substring-matched prose | caught by **2**: `test_no_script_uses_minimize` (static) and `test_the_rmsd_function_measures_displacement_rather_than_shape`, which measures a rigid 3.0 Å translation as `0.00000 A` |
| `seed = 42` → `seed = 0` in `ch09_first_run/config/vina_config.txt` | caught by **1**, and not the intended one: `test_seed_is_cross_checked_between_config_and_log`. The reproducibility test never read the config | caught by **3**: that cross-check, plus `test_no_vina_config_leaves_the_seed_at_the_random_default` (parses the value) and `test_the_configured_seed_actually_reproduces` (docks twice at the config's own seed; two different SHA-256s) |
| file-order ligand selection | caught by **1**, and by copy identity rather than by distance — the distance assertion held, because 1L2S's first copy is also 2.70 Å from a Ser64 OG | caught by **4**: two in `test_gotchas` on a synthetic case where order and distance disagree, two in `test_ch20` on the worked example |

One correction to the original re-scoping, which still stands: **there is no
file-order selection in ch05 to mutate.** `qc_report.py` reports every copy and
iterates `site_ligands`; it never chooses one. The mutation was applied where
selection actually happens — `receptor_prep.select_copy`, which the seven
selecting chapters now all call.

Worth recording: under the `minimize=True` mutation the ch17 RMSD-*value* tests
still pass. Superimposing two different conformers does not give zero, so
`rmsd > 0` holds. The behavioural test is not duplicating an existing guard.

### Findings closed

| | Finding | Commit |
|---|---|---|
| **B1** | ch20's tests asserted a state the suite never built | `26f6dcb` — fixture builds ch09's AmpC branch; verified by deleting `ch09_first_run/outputs/ampc` |
| **B2** | the loud error message guarded the file that is never missing | `26f6dcb` — both inputs refused alike, naming file and chapter |
| **B3** | unguarded SDF reads traceback on bad input | `0b5b7ab` — `scripts/molfile.py`; **eleven** call sites, not eight (the report missed ch26 and `data/ligands/generate.py`) |
| **B6** | ch24's refusal asserted by nothing; 16 chapters had no test file | `783d01d` — all 16 covered, 98 → 247 tests |
| **B7** | three tests weaker than their names promise | `c3fda90` — see the mutation table above |
| **B8** | `pip install -r requirements.txt` cannot succeed on Windows | `d177a6a` — and it is worse than reported: pip abandons the transaction, so **nothing** installs, not "everything but Vina" |
| **B9** | `pytest` missing from `requirements.txt` | `d177a6a` |
| **B10** | Open Babel on Windows undocumented and misdescribed | `d177a6a` — `openbabel-wheel==3.1.1.23` named, together with the fact that it gives Open Babel **3.1.0**, not the pinned 3.2.1 |
| **B11** | ten undeclared cross-chapter dependencies | `4606bde` — twelve edges declared, plus two guards derived from the code |

Three defects **not** in the original list were found while fixing B6, all in
ch02 and all of the same family the report is about — silent degradation that
leaves a report looking complete:

- Two of seven criteria used `if data is not None:` with no `else`. With ch14 or
  ch16 unrun their rows vanished entirely: six findings, zero gaps, nothing
  saying a question had been dropped. The chapter's stated contract is that a
  missing source reports NOT MEASURED.
- `ch26_case_study` was listed in `SOURCES` and never loaded, so the chapter
  advertised a dependency it did not have.

Both were found by parametrizing the missing-source test over every source.
Testing only the one source that happened to be handled correctly is how they
survived — the same shape as B7.

### Findings still open

| | Finding | Why it is still here |
|---|---|---|
| **B4** | `ch09/run.sh` rewrites a tracked config whose only diff is a timestamp | not in the fix list. The test fixtures deliberately do not run `derive_box.py`, so the suite does not make it worse |
| **B5** | the ch08 conformer mutation is invisible on Windows | not in the fix list, and it is a decision rather than a repair: whether a Windows-only run may report success for ch08 at all |
**B12 is now closed** — `docking_common.dock()` refuses a best affinity of 0 or
above, printing the log and naming the box centre and size it used. Every Vina
call in the repository goes through that function, which is what makes one
check sufficient. Guarded from both sides:
`test_a_box_that_misses_the_receptor_is_refused_rather_than_scored` drives the
real failure with a box centred 100 Å away, and
`test_a_box_that_covers_the_receptor_still_docks` exists so a `dock()` that
refused everything would not pass.

**B5's open question is answered** — see the Linux section below. All fifteen
ch08 conformer counts match the book on the reference platform, where the xfail
marker does not apply and the tests run unprotected. The Windows blindness the
finding describes is unchanged and is by design; what is no longer open is
whether the book's counts were right.

**B13 is now closed** — the `|| true` is gone from both `run.sh` files and each
propagates its script's exit code; both chapters exit **3** here. The footer
still prints, so a reader without a GPU is still told where the input file they
*can* check was written. Guarded by
`test_run_sh_propagates_the_scripts_exit_code` (ch13) and
`test_run_sh_propagates_the_gnina_pipelines_exit_code` (ch16), which assert the
wrapper's code *equals* the script's rather than that it is non-zero — so the
guard still holds on a machine that has a GPU or GNINA.

Note the consequence for check 5 above, which recorded "all 25 chapters run end
to end from a foreign working directory. **Every one exits 0.**" That is
deliberately no longer true: two of them now exit 3, because they could not do
the thing they are for.

### Check 4, re-run against the new suite

Of the six §6 values the report found genuinely unchecked, **three are now
asserted**: ch14's `0.38`, ch16's `0.90`, ch26's published `1.75`/`1.87`.

**Three remain unchecked**, and all three are the synthetic receptor recipe in
`ch09_first_run/scripts/make_test_system.py` — `SHELL_ATOMS = 140` and the
9.0–10.5 Å shell. They are named constants that nothing asserts. ch09's timings
(3.4 s, 14.2 s) remain correctly uncovered: §6 says to assert the ratio, and the
ratio is asserted.

### The Linux install path — now executed

This was the largest thing the original report could not do. It has been done:
**Ubuntu 24.04.4 LTS, Python 3.12.3** — the stock Python of that release, and
the version the book names — installed as a second WSL distribution, fresh
clone, `environment/README.md` followed literally.

The full account is in PROGRESS.md. Three findings in the documented install:

- **L1** `python3.12 -m venv .venv`, the README's first line, **fails** on a
  stock Ubuntu 24.04. Debian and Ubuntu ship `venv` without `ensurepip`;
  `python3.12-venv` is an undocumented prerequisite.
- **L2** `sudo apt install openbabel` gives **3.1.1**, not the pinned 3.2.1,
  and no form of the command will produce 3.2.1 from Ubuntu's repository. Taken
  with B10, the pin is now known to be unobtainable by the documented route on
  both platforms.
- **L3** `pip install -r requirements.txt` **succeeds** — and the repository
  still cannot dock anything. `pip install vina` gives the Python bindings;
  there is no `vina` command, and every script here calls Vina through its
  command line. `pytest` after the documented install: **69 errors, 4
  failures**, all of them the clean `Vina not found` message with no traceback.
  The README's Windows section tells you to fetch the binary. Its Ubuntu
  section did not — on the platform the book's numbers come from.

All three are fixed in `environment/README.md` and annotated in
`requirements.txt`.

**With the binary in place: 245 passed, 2 failed, and no xfail or xpass at
all** — on Linux `platform_xfail` does not apply, so every value it protects on
Windows was asserted outright.

The box sweep returned **−4.905 / −4.911 / −2.748**, largest difference from
the book **0.000 kcal/mol**. The reference-platform claim that runs through this
whole repository is verified rather than asserted, for the first time.

Of the two failures, one was an over-assertion of mine in ch07 and is removed.
The other is an **open disagreement with the book**: CLAUDE.md section 6's
exhaustiveness ratio band of 3–5 does not hold. Best-of-3 on an idle machine
gives **2.80 on Linux** and 3.34 on Windows, against the book's own 4.18. The
mechanism is in `timing.py`'s own docstring — the grid is a fixed cost, this
machine is about twice as fast as the book's, so the ratio compresses. It is
recorded as a non-strict xfail carrying the measurements, **not** tuned to fit,
and it needs an author decision. PROGRESS.md sets out the three options.

### What is still not verified

Check 7's subjective half was skipped on purpose, and a Windows-only run still
cannot police ch08's protonation order (B5) — that is the finding, not a gap
in the fixing.

### B7's shape, found twice in the tooling

Two errors during the root restructure had the same shape as B7, and neither
was in the repository's code — both were in how its state was being checked.

**A pipeline's exit code is the last command's.** Three full-suite runs were
reported as `exit 0` on the strength of `pytest -q | tail`, which reports
`tail`'s status. `tail` cannot fail. The runs happened to be clean, so nothing
false was recorded, but the evidence cited was not evidence, and the third run
printed a complete `AssertionError` traceback *underneath* the same `exit 0`.

**A byte count read through a formatter is not a byte count.** `od -c | grep -o
'\\r'` reported 56 CR bytes in a shell script that `bash -n` had just parsed
without complaint. Counting the bytes directly gave zero. The formatter's
rendering, not the file, was being matched.

The defect they hid was real: rewriting files with Python's `write_text` on
Windows translates `\n` to `\r\n`, and `.gitattributes` here says
`* text=auto eol=lf` precisely because `ch16_rescoring/scripts/rescore_with_gnina.sh`
fails at `set -euo pipefail` with `invalid option name` when it carries CRs.
Committed content was never at risk — git normalises on commit — but the
working tree was broken, and **only the full suite catches this class of error,
because only it executes the `.sh` files.**

**What caught both was contradiction, not care.** A traceback beside a success
status; a CR count beside a file bash had just parsed. Re-reading either
command would not have helped — both were doing exactly what they said. The
general rule, which is `CLAUDE.md`'s *compute a number twice by different
routes* applied to tooling rather than to chemistry:

> When a tool's output is a summary rather than the thing itself, verify it by
> a differently-shaped route.

An exit status summarises a run; read the run. A formatter's rendering
summarises bytes; count the bytes. This is the same failure B7 names — a check
that reports protection it is not providing — and it is worth recording that it
appeared in the instruments rather than in the code, where the suite cannot
reach it.

### The same shape, kept as a list

B7 was not a one-off, and the tooling pair above was not the end of it. Every
entry below is a check that passed while providing less protection than its
name claimed. None was found by reading it.

| The check | What its name claimed | What it actually tested | Caught by |
|---|---|---|---|
| `test_the_rmsd_call_passes_minimize_false_explicitly` | that the RMSD call does not superimpose | that the string `minimize=False` occurs in the file — prose counted | mutating `minimize=False` to `True` |
| `pytest -q \| tail` | a clean suite, on `exit 0` | `tail`'s exit status, which cannot be non-zero | a full traceback printed above that same `exit 0` |
| the site's internal-link check | that all 31 links resolve, the 25 chapter routes as 302 | it would have tested GitHub's status for the destination, not Netlify's for the route: a route serving 301, or serving nothing, still looks healthy once you follow it | asking what a wrong status would have looked like — fixed before it ran, by not following |
| `python -m http.server` as a site preview | that the site serves | a different site. No clean URLs, `_redirects` ignored, its own 404 in place of `404.html` — so the three things a printed address depends on are the three it cannot show | `/setup` and `/ch09` 404ing locally while being correct; replaced by `scripts/preview_site.py` |
| `test_the_guess_was_wrong_by_about_two_decades` | that the ch25 guess was two decades low | `ki / guess > 1.5`, which 1.8× satisfies | the pre-publication prose review |
| `test_the_conversion_is_the_textbook_one_and_still_fails` | that ch25 converts ΔG with the textbook constant | agreement to `rel=0.02` — and a wrong RT fits inside 2% with room to spare | fixing the row above it |

Two of the six were caught before they ever ran and four only afterwards,
which is the one encouraging thing here: the shape is becoming recognisable
early.

**The ch25 entry is the one where the claim, not the check, was the defect.**
The guess is 10 µM against measured 18, 26 and 26 — low by 0.26 to 0.41
decades, not two. `DECADES_BELOW = 2` describes how far the *design* extends
below the guess, and the number migrated from the width to the error, taking
with it a second slip in the same paragraph: a conversion wrong by 6.6×, 15.3×
and 16.5× was described as two orders of magnitude rather than one. An
assertion of `> 1.5` cannot discriminate 0.41 decades from 2.0, which is
precisely what left the name free to say something the code never tested.

Corrected across the script, its generated report, the chapter README and the
test, and the replacement was mutation-checked the way the B7 fixes were: with
`guess = 1.0` — a guess that genuinely *is* two decades low —
`test_the_guess_was_low_by_under_half_a_decade` and
`test_the_width_is_chosen_before_the_error_can_be_known` both fail, where the
old assertion passed comfortably at 26×.

The argument the chapter makes now is the one that survives the correction: the
four-decade width cannot be justified by how wrong the guess turned out to be,
because that is unknowable while the plate is being designed. It is justified
by how little *was* bounded at design time — the naive conversion offers
1.17–3.91 µM and is itself wrong by an order of magnitude, and the docking
score bounds nothing at all.

**The sixth entry came out of fixing the fifth**, which is the argument for
keeping this list. Correcting ch25's prose exposed a second, quieter drift:
the chapter README's conversion table read 3.86 / 1.16 / 1.55 µM where the
script wrote 3.91 / 1.17 / 1.57. All three README values are internally
consistent with RT at T = 297.8 K against the script's 298.15 — a table copied
by hand once, under an older constant, and never recomputed. The test named for
exactly this, `test_the_conversion_is_the_textbook_one_and_still_fails`,
recomputed the conversion and then accepted it to `rel=0.02`. The discrepancy
is 1.25%. A tolerance chosen to be safely loose was loose enough to admit the
one thing the test existed to reject.

Both are closed, and closed structurally rather than by correcting the digits.
The tolerance is now `rel=1e-9`, which is the honest figure for a test that
recomputes the identical expression: anything above float noise means the
constant moved. The README table is no longer typed at all — it is lifted from
the report the script writes, and `test_the_readme_table_is_the_generated_one`
compares the two on every run. Mutation-checked both ways: restoring T = 297.8 K
fails three tests where it previously failed none, and changing a single digit
in the README table fails the comparison.

The rounding defect underneath it is closed the same way. `conversion_error_fold`
was stored as `round(x, 1)` and then formatted `%.0f`, so 16.52 became 16.5
became **16×** in the written report while stdout formatted the raw value to
**17×** — one run, one quantity, two published numbers. The payload now carries
raw floats and rounding happens once, where a number is displayed.

### Verification of the fixes

Each of the six commits was followed by a clean-clone run — a fresh `git clone`
of the committed state, provisioned as `environment/README.md` instructs, with
`PATH` scrubbed of the parent repository's `.venv/Scripts`. Not `pytest` in the
working tree, which is the check that failed originally and the only one that
proves a reader can use this.

The final run, at `4606bde`, re-ran `data/structures/fetch.sh` as well: four
checksums matching `data/structures/README.md`, then **247 tests, exit 0**, 3
xfailed and 1 xpassed as before.

The install path was additionally provisioned from scratch once, following the
newly written Windows section literally rather than reusing a virtualenv:
`pytest` arrived from `requirements.txt`, `obabel -V` reported 3.1.0, and the
suite passed. That run is what exposed `requirements-windows.txt` appearing in
`git status`, fixed in `595cee5`.

The clone is left provisioned and clean at `…/scratchpad/clonetest` for reuse.
