# Stress report

Results of `STRESS_TEST.md`, run against commit `79e26b8` on Windows 11,
Python 3.12.10.

**All seven checks were attempted. Nothing was fixed.** Every mutation was
reverted before the next; the clone and the working repository both end clean.
Total elapsed: 30 minutes of the two-hour budget.

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

## Resume here

Nothing is outstanding: all seven checks were attempted and the two skipped
items are skipped on purpose (check 7's subjective half; the Linux install-path
verification, which this machine cannot perform).

If this is picked up again, the three things worth doing, in order:

1. **Fix B1 and B2 together.** Give the missing log the same `sys.exit` the
   missing config already gets, and make the ch20 tests either run
   `ch09_first_run/run.sh` first or pass `--log` explicitly. B2 is the root
   cause; B1 is what it allowed.
2. **Verify the documented install on Ubuntu with Python 3.12** — `pip install
   -r requirements.txt`, then `pytest`. This is the repository's core claim and
   it has never been executed. B8, B9 and B10 are all in that path.
3. **Decide what to do about B5.** Keeping the non-strict marker is right; the
   question is whether a Windows-only run should be allowed to report success
   for ch08 at all, given it cannot police the protonation order.

The clone is left provisioned and clean at
`…/scratchpad/clonetest` for reuse.
