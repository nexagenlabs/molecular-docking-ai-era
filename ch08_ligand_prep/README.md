# Chapter 08 — ligand prep

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch08_ligand_prep/run.sh
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

RDKit ETKDGv3, 300 attempts, `pruneRmsThresh=0.5`, seeds 1 / 7 / 42 / 99 / 2026:

| Ligand | Rotatable bonds | Conformers by seed |
|---|---|---|
| STC | 4 | 17, 16, 15, 16, 15 |
| 18U | 6 | 10, 14, 9, 9, 9 |
| 1MU | 7 | 33, 39, 33, 30, 40 |

Conformer counts do **not** track rotatable-bond count — 18U has more rotatable
bonds than STC and yields fewer conformers. That is the teaching point of the
chapter, not a bug to be fixed.
