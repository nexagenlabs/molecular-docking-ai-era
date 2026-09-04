# SESSION_PLAN.md

An autonomous build plan for this repository. Read `CLAUDE.md` first; this file
assumes it.

---

## How to run this session

Work through the phases in order. **Each phase has an exit gate. Do not begin a
phase until the previous gate passes.**

Maintain `PROGRESS.md` at the repository root, updating it after every completed
task. It is the session's memory: if this session ends or is interrupted, the
next one reads `PROGRESS.md` and resumes without repeating work.

```markdown
# PROGRESS

## Phase 0 — foundation
- [x] directory skeleton
- [ ] environment.yml
...

## Blocked / needs a decision
- (nothing yet)

## Deviations from CLAUDE.md
- (nothing yet)
```

### Working in bounded batches

This is a long session and context is finite. Phase 3 alone has seventeen
chapters, which will not fit in one stretch of working memory.

**Complete one chapter, commit it, update `PROGRESS.md`, and only then read
the next chapter's requirements.** Do not load several chapters' worth of
context at once, and do not keep large file contents in memory after you have
finished with them.

If you notice your context filling, stop at the current chapter boundary,
write a short handover into `PROGRESS.md` under a heading `## Resume here`
naming the next task and anything in flight, and say plainly that you are
stopping for context rather than because the work is done. A clean stop with
a resumable state is a success; running out mid-chapter is not.

### Commits

Commit after every completed task, not at phase boundaries. Message format:

```
ch09: derive box from reference ligand centroid
tests: assert seed 42 reproducibility
phase0: repository skeleton and environment
```

Small commits make a wrong turn cheap to undo, which matters more in an
unsupervised run than in a supervised one.

### Three standing rules

**1. Stop on unexpected results, do not work around them.**
If a script produces a value that disagrees with section 6 of `CLAUDE.md`, do not
adjust the script to match. Record it under "Blocked" in `PROGRESS.md` with both
numbers and what you think caused it, and move to the next task. A disagreement
is information; a silently corrected script is a lie.

**2. Never invent a value.**
If a number is needed and is neither in `CLAUDE.md` nor obtainable by running
something, write `TODO(value)` and record it as blocked. Plausible placeholders
are worse than gaps because they survive review.

**3. Run what you write.**
Every script must be executed before you mark its task complete. "It should work"
is not complete. If the environment prevents running it — no GPU, no network —
say so in `PROGRESS.md` and mark the task partial rather than done.

---

## Phase 0 — Foundation

Nothing here depends on chemistry, so get it exactly right before anything else.

### 0.1 Skeleton

Create the directory structure from `CLAUDE.md` section 2, including all 25
chapter directories from the list there. Each chapter directory gets a stub
`README.md` containing only its title and a one-line statement of what it will
do. No code yet.

### 0.2 Repository files

- `.gitignore` — from `CLAUDE.md` section 8.
- `LICENSE` — MIT, copyright Suryaprakash Tripathy / NexaGenLabs.
- `README.md` — placeholder for now; written properly in Phase 4.
- `errata.md` — a heading and an empty table.
- `PROGRESS.md` — as above.

### 0.3 Environment

`environment/environment.yml` with the pins from `CLAUDE.md` section 4. Create the
environment and record the **resolved** versions of every package in
`environment/resolved.txt`. The pins say what you asked for; `resolved.txt`
records what you got, and the difference matters when a reader's numbers differ.

### 0.4 The test harness — build this before any chapter code

`tests/` with pytest, containing one test module per chapter that has expected
values in `CLAUDE.md` section 6. Each test asserts a published value by
invoking the chapter's `run.sh` or script **as a subprocess**, never by importing
it. Import-based tests cannot even be collected before the code exists; a
subprocess call fails cleanly with a missing-file error, which is what you want.
All of these will fail now. That is correct and expected.

Write these first:

| Test file | Asserts |
|---|---|
| `test_ch04_formats.py` | PDBQT round-trip changes net charge from −2 to 0 and reorders atoms; PDB and MOL2 round-trips preserve canonical SMILES exactly |
| `test_ch08_ligand_prep.py` | Net charges STC −1, 18U −2, 1MU −2; conformer counts match the table for seeds 1/7/42/99/2026 |
| `test_ch09_first_run.py` | Two runs at seed 42 identical; two at seed 0 differ; box 20/12/8 Å give −4.905/−4.911/−2.748 |
| `test_ch10_flexibility.py` | Rotamer analysis returns exactly {Gln120, Leu293, Thr316} |
| `test_ch17_validation.py` | Ligand selection picks the copy 2.70 Å from Ser64 OG, not the 22.7 Å one; RMSD computed without superposition |
| `test_ch18_enrichment.py` | Both screens give AUC 0.758; EF1% 56.0 and 0.0; BEDROC 0.574 and 0.058; agrees with RDKit's `CalcBEDROC` to 6 dp |
| `test_ch21_md.py` | Window means 1.10/1.47/1.90/2.34 Å at 1/10/100/1000 ns |

Use `pytest.approx` with a tolerance you state in a comment. For values the book
prints to three decimals, use `abs=0.001`.

Add `tests/test_gotchas.py` asserting the three items in `CLAUDE.md` section 5:
that no script in the repository contains the string `--minimize`, that no Vina
config leaves `seed` unset, and that the format checker flags PDBQT charge loss.

**Gate 0:** `pytest --collect-only` succeeds and lists every test. All tests fail
when run, and each failure is a missing chapter script rather than a Python
error. The skeleton is complete and `environment/resolved.txt` exists. Commit.

---

## Phase 1 — The pattern chapter

Build `ch09_first_run` completely. Everything after this copies its shape, so
spend disproportionate care here.

### 1.1 Contents

- `README.md` — what it does, how to run it, what to expect, roughly 300 words.
- `config/vina_config.txt` — receptor, ligand, box, `exhaustiveness = 32`,
  `num_modes = 9`, `energy_range = 3`, **`seed = 42`**, with a comment on each
  line saying where the value came from.
- `run.sh` — one command, start to finish, `set -euo pipefail` at the top.
- `scripts/derive_box.py` — computes the box from the reference ligand centroid
  and **writes the numbers into the config**, so the centre was computed rather
  than typed.
- `scripts/verify_run.py` — reruns at the same seed and asserts byte-identical
  output; reruns at seed 0 twice and asserts they differ.
- `scripts/timing.py` — measures exhaustiveness 8 against 32 and reports the
  ratio.
- `outputs/expected/` — the reference poses, log, and a `checksums.txt`.

### 1.2 What ch09 docks into

The book's Chapter 9 timings and box-size results were measured on a **small
synthetic system**, not on AmpC: a ten-heavy-atom ligand against a shell of
carbon atoms forming a crude pocket. That was deliberate, so the measurements
are cheap and anyone can repeat them in seconds.

So this chapter needs two inputs, and they are different things:

- `scripts/make_test_system.py` — builds the synthetic receptor and ligand
  from a fixed seed. This is what the timing and box-size numbers refer to,
  and what the tests assert against.
- The AmpC system from `data/` — what a reader actually docks once they have
  worked through the demonstration.

`run.sh` should do the synthetic demonstration first, then the AmpC run. Keep
them clearly separate in the README; conflating them is how a reader ends up
expecting 14 seconds on a real protein.

### 1.2 The teaching content must survive

This chapter's job is to demonstrate three things. If the code works but does not
show them, the chapter has failed:

- The default seed is random. `verify_run.py` must print both outcomes side by
  side so the difference is visible, not merely asserted.
- Undersized boxes fail silently. Include a script that runs 20/12/8 Å and prints
  all three scores with no error, and a comment naming this as the point.
- Mode 1's RMSD columns read `0.000 0.000` by construction and are not
  validation. Print them and say so in the README.

**Gate 1:** `pytest tests/test_ch09_first_run.py` passes and `run.sh` completes
from a clean checkout.

On which values must match: the **seed behaviour** and the **box scores**
(−4.905 / −4.911 / −2.748) are deterministic and must match exactly. The
**timings are hardware-specific** — 3.4 s and 14.2 s were measured on four cores
with a small ligand, and your absolute numbers will differ. Assert only that the
ratio is between 3 and 5, and record your actual timings in `PROGRESS.md` so the
book can carry a hardware note.

Commit, then **report before starting Phase 2**, including any value that
differed and which side you think is wrong.

---

## Phase 2 — Chapters with hard expected values

These have assertions in section 6, so correctness is checkable. Build in this
order; each depends on the last.

**2.1 `ch05_receptor_prep`** — QC report for any PDB entry: resolution, R-free,
gaps (REMARK 465), missing side chains (REMARK 470), altlocs, every HETATM group
with its distance to Ser64 OG, and bridging waters within 3.5 Å of both ligand
and protein. Must reproduce, for **1L2S**: three STC copies at 2.70, 2.70 and
22.7 Å from Ser64 OG; chain A missing 290–292; sole altloc Gln250; two bridging
waters in chain B. And separately, for **4JXS, 4JXV and 1GA9**: the nearest
phosphate phosphorus to any Ser64 OG is 7.83 Å. **1L2S contains no phosphate** —
if your script reports one there, the ligand selection is wrong.

**2.2 `ch08_ligand_prep`** — Protonation at pH 7.4, stereochemistry round-trip
check, conformer generation. **Assert the charges as a hard failure**, not a
printed line: if a future RDKit changes protonation behaviour the build must
break loudly.

**2.3 `ch04_formats`** — The round-trip experiment. Must show that PDB and MOL2
are safe and PDBQT is not. The README must correct the folklore explicitly.

**2.4 `ch17_validation`** — Full specification in `CLAUDE.md` section 7. The most
load-bearing script in the repository. It must print every HETATM group it did
not use. Report the three RMSD values it produces; they fill placeholders in the
book.

**2.5 `ch18_enrichment`** — Generate the two screens, compute AUC, EF and BEDROC,
cross-check BEDROC against RDKit. The notebook must plot both screens so the
identical AUC and divergent early enrichment are visible.

**2.6 `ch10_flexibility`** — Torsion angles across four structures and eight
chains; report which residues change rotamer.

**2.7 `ch21_molecular_dynamics`** — The synthetic convergence demonstration. The
GROMACS pipeline itself is Phase 3; this task is only the convergence notebook,
which needs no MD software.

**Gate 2:** all Phase 2 tests pass. Commit after each chapter, not in a batch.
Report every value that differed from section 6.

---

## Phase 3 — Remaining chapters

No hard expected values, so the standard is different: **each must run end to end
and produce something a reader can inspect.** A directory containing only a
README is not complete.

Where a chapter needs software that may be unavailable (GROMACS, GNINA, Boltz-2,
a GPU), write the pipeline, attempt it, and if it cannot run here, say so in the
chapter README and in `PROGRESS.md`. Do not fake outputs.

`ch02_method_choice` · `ch03_databases` · `ch06_predicted_structures` ·
`ch07_pocket` · `ch11_web_servers` · `ch12_screening` · `ch13_cofolding` ·
`ch14_boltz2` · `ch15_cofolding_field` · `ch16_rescoring` ·
`ch20_protocol_record` · `ch22_free_energy` · `ch23_interactions` ·
`ch24_network_pharmacology` · `ch25_hit_to_bench` · `ch26_case_study` ·
`ch27_methods`

Three of these carry specific requirements:

- **`ch20_protocol_record`** — the blank record, the filled AmpC example, and a
  script that populates most fields from a config file and a run log. The filled
  example must match the book: 1L2S **chain B**, R-free 0.207, STC copy B/2115,
  altloc Gln250, no metal.
- **`ch24_network_pharmacology`** — must refuse to run without an explicit
  background gene list. That refusal is the chapter's argument.
- **`ch26_case_study`** — the three reproduction tests with published answers
  from section 6.

**Gate 3:** every chapter directory has a runnable `run.sh` or notebook, or a
README stating exactly why it cannot run in this environment.

---

## Phase 4 — Integration

### 4.1 Root README

Written last, when you know what is actually there. Include: what the repository
is, the one-paragraph AmpC description, how to install, how to run one chapter,
the licence split (**code MIT; book text and figures not covered**), and a table
of chapter directories with one line each and a link.

### 4.2 Cross-checks

- Every directory named in `CLAUDE.md` section 2 exists.
- No file contains `--minimize`.
- No Vina config leaves the seed unset.
- Every `run.sh` starts with `set -euo pipefail`.
- No fabricated numbers: grep for `TODO(value)` and list what remains.
- `pytest` passes, or every failure is recorded in `PROGRESS.md` with a reason.

### 4.3 Final report

Write `BUILD_REPORT.md`: what was built, what runs, what could not run here and
why, every value that differed from section 6 with your assessment of which side
is wrong, and every open `TODO(value)`.

**Gate 4:** report delivered.

---

## When you are unsure

Four situations, four responses.

**A value disagrees with the book.** Record both numbers and your diagnosis in
`PROGRESS.md`. Do not change either. Continue.

**Software is unavailable.** Write the pipeline anyway, attempt it, document the
failure. Do not simulate output.

**A design decision is not covered here.** Choose the option that makes the
result easier for a reader to check, and record the choice under "Deviations".

**The network is unavailable for PDB fetches.** Note it, and continue with the
tasks that do not need structures. Do not commit downloaded structures either
way; `data/structures/fetch.sh` is the deliverable.

---

## What finished looks like

A reader clones the repository, creates the environment from `environment.yml`,
runs `bash ch09_first_run/run.sh`, and sees the numbers printed in Chapter 9 of
the book. Then they do the same for any other chapter.

If that works, the repository has done its job. If it does not, nothing else in
it matters.
