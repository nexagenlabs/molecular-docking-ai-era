# Chapter 21 — molecular dynamics

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch21_molecular_dynamics/run.sh
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

Synthetic trajectory built from four separated relaxation timescales:

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window |
|---|---|---|---|
| 1 ns | 1.10 Å | −0.150 Å/ns | 1.45 Å |
| 10 ns | 1.47 Å | −0.010 | 1.99 Å |
| 100 ns | 1.90 Å | +0.007 | 2.37 Å |
| 1000 ns | 2.34 Å | +0.0004 | — |

Every window looks converged by its own flat-tail test. The 10 ns answer is 37%
below the 1000 ns one.
