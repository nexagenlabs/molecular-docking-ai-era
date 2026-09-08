# STRESS_TEST.md

The repository passes its own test suite. That is weaker evidence than it looks,
because the tests were written by the same process that wrote the code. These
checks attack it from outside instead.

Work through them in order. Record every result in `STRESS_REPORT.md`, including
the ones that pass. **Do not fix anything while testing** — a fix made mid-test
invalidates everything after it. Test first, report, fix second.

---

## 1. The clean-clone test

The suite has only ever run in the environment that built it, which has
accumulated state. Nothing proves a stranger can reproduce anything.

```bash
cd /tmp && rm -rf clonetest
git clone <local repo path> clonetest && cd clonetest
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash data/structures/fetch.sh
pytest
```

Record: what failed, and whether each failure is a missing input, a missing
install step the README does not mention, or a genuine defect.

**This is the single most important check on the list.** Everything else
assumes it passes.

---

## 2. Mutation testing — do the tests detect anything?

A test that never fails is decoration. Break things deliberately, one at a time,
and confirm the suite catches each. **Revert after every one.**

| Mutation | Which test should fail |
| --- | --- |
| In ch09's config, change `seed = 42` to `seed = 0` | the reproducibility test |
| In ch08, generate conformers on the neutral form | the conformer count test |
| In ch17's RMSD call, add `--minimize` | the gotcha test, and the RMSD values |
| In ch05, select the first HETATM group instead of by distance to Ser64 | the ligand-copy test |
| In ch18, re-seed the generator inside the search loop | AUC, EF and BEDROC |
| In ch24, supply a whole-genome background instead of the predictor's space | the refusal test |
| In `data/ligands/generate.py`, skip deprotonation | the charge assertion |

Any mutation the suite does not catch is a hole. Name it in the report.

---

## 3. Adversarial inputs

Each script should fail with a clear message, not a traceback or a wrong answer.

- A PDB entry that does not exist (`9ZZZ`)
- A structure with no ligand at all (fetch an apo entry)
- A ligand SMILES that will not parse (`C1CC`)
- An empty SDF
- A receptor and ligand whose coordinates do not overlap the box
- `run.sh` invoked from a different working directory

The last one catches hard-coded relative paths, which is the commonest way a
repository works only for its author.

---

## 4. Book-to-code agreement, checked in the other direction

The tests assert that the code produces the book's values. Check the reverse:
that every value in `CLAUDE.md` §6 is actually asserted somewhere.

Write a script that parses §6, extracts each numeric claim, and greps the test
suite for it. Report any value in the book that **no test checks**. Those are
claims nobody is verifying.

---

## 5. Documentation honesty

For each of the 25 chapters, confirm that its `README.md` describes what
`run.sh` actually does. Specifically:

- Does every command in the README exist and run?
- Does the README claim any output the script does not produce?
- Do the three chapters that cannot run here say so plainly, rather than
  implying success?

---

## 6. The xfail audit

Three tests are marked expected-to-fail and one reports XPASS. For each:

- Is the stated reason still true?
- Would it pass on Linux? Confirm rather than assume.
- Is any xfail masking a real defect rather than a platform difference?

An xfail is a claim about why something fails. Unexamined, it becomes a place
where failures hide.

---

## 7. Fresh-eyes read

Pick three chapter directories at random. For each, read only the README and
try to run it without consulting any other file. Note every point where you had
to guess. That is what a reader experiences.

---

## What to report

`STRESS_REPORT.md`: what passed, what failed, and for each failure whether it is
a defect in the code, a gap in the documentation, an environment problem, or a
disagreement with the book. Do not fix anything until the report exists.
