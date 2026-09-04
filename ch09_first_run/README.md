# Chapter 09 — first run

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch09_first_run/run.sh
```

Requires the pinned environment — pip, Python 3.12.3, see
[`environment/README.md`](../environment/README.md):

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## What to expect

_To be written._ Reference results will live in `outputs/expected/`, so you can
tell whether your run matched without opening the book.

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

This is the sample chapter and the pattern the other chapters follow.
