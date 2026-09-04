# Chapter 9 — your first docking run

Four demonstrations of how a docking run can go wrong while looking as though
it went right.

## Run

```bash
bash ch09_first_run/run.sh
```

One command, start to finish: it fetches 1L2S if it is missing, builds the
ligand reference copies if they are missing, prepares the receptor and ligand,
runs the four experiments, and writes `outputs/results.md`. Pass `--quick` to
skip the exhaustiveness-32 timing run.

Requires the pinned environment — pip, Python 3.12.3, see
[`environment/README.md`](../environment/README.md):

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Vina is found through `$VINA`, then `.tools/`, then `PATH`. It must report
1.2.7.

## What this does

`prepare_inputs.py` builds the inputs and prints every decision it makes:

- Picks the STC copy **by distance to Ser64 OG**, not by file order. 1L2S holds
  three; the script prints all three with their distances and discards B/3115
  at 22.72 Å.
- Prints **every HETATM group it did not use**, by name. A ligand quietly
  mis-picked is the failure this guards against, and it happens through a group
  nobody mentioned.
- Names HOH 403 and 481 specifically. They bridge the ligand to the protein at
  2.68 and 2.70 Å; this chapter deletes all waters, which is the usual default
  and is a decision, not a neutral act.
- Uses chain B, because chain A is missing Lys290–Ala292.
- Types ten disordered chain B side chains as alanine. REMARK 470 says they are
  missing their distal atoms, so what the file contains is exactly alanine's
  heavy atoms. Deleting the residues instead would remove backbone, and
  Lys290's centre of mass is 1.1 Å outside the 20 Å box face.

`experiments.py` then runs the four demonstrations and writes
`outputs/results.md` next to `outputs/expected/results.md`.

## What to expect

Compare your `outputs/results.md` against
[`outputs/expected/results.md`](outputs/expected/results.md), which carries the
book's values, this repository's values, and — for the box-size experiment —
an unresolved discrepancy between them that is documented rather than papered
over.

## Values this chapter must reproduce

Vina 1.2.7:

- Seed 0 twice → different results. Seed 42 twice → byte-identical.
  Vina's default seed is 0, which means *random*; nothing in the log
  distinguishes a defaulted seed from a fixed one.
- Exhaustiveness 8 → 3.4 s; exhaustiveness 32 → 14.2 s on 4 cores (factor 4.2).
- Box edge 20 / 12 / 8 Å → best score −4.905 / −4.911 / −2.748.
  **No error is raised** when the box is too small to hold the ligand.
- Mode 1 always reports RMSD `0.000 0.000`. That is the distance from mode 1,
  not from a crystal pose — it is not a validation result.

Three of the four reproduce. The box-size *scores* do not: this repository gets
−7.384 / −7.410 / −6.837 on the same three box sizes. The behaviour the chapter
teaches does reproduce — no error at any size, 20 Å and 12 Å within 0.03 of each
other, 8 Å worse than both — but the absolute numbers differ by about
2.5 kcal/mol. Two hypotheses have been tested and rejected (bridging waters
kept; a naive centroid over all three STC copies). See
`outputs/expected/results.md` for what is still open. **Do not tune the script
to close the gap** — that would destroy the evidence needed to work out which
side is wrong.

This is the sample chapter and the pattern the other chapters follow.
