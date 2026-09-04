# Chapter 04 — formats

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch04_formats/run.sh
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

Round-trip a charged ligand through each format and compare canonical SMILES.

| Format | Charge | Bond orders | Stereochemistry | Atom order |
|---|---|---|---|---|
| PDB | preserved | preserved | preserved | preserved |
| MOL2 | preserved | preserved | preserved | preserved |
| PDBQT | **lost** — the 18U dianion returns neutral | — | — | **changed** |
| XYZ | **lost** | — | — | — |

Open Babel re-perceives chemistry from the 3D coordinates, so the folklore that
PDB destroys bond orders and stereochemistry is out of date. PDBQT is the format
that actually loses information, and it is the one docking uses.
