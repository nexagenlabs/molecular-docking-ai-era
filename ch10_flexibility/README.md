# Chapter 10 — flexibility

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch10_flexibility/run.sh
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

Torsion analysis across the four structures (1L2S, 4JXS, 4JXV, 1GA9), eight
chains, over the binding-site residues. Eight of the thirteen site residues vary
by ≤20° in every torsion. The analysis must return

**Gln120, Leu293 and Thr316**

as the rotamer-changing residues — the only defensible choices for flexible
side-chain docking here.
