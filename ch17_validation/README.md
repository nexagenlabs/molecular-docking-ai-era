# Chapter 17 — validation

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch17_validation/run.sh
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

## Specification

The most load-bearing script in the repository. It must:

1. Fetch 1L2S, 4JXS and 4JXV from `files.rcsb.org`.
2. Separate receptor from ligand, and **print every HETATM group it did not
   use**. Silent ligand mis-picking is the failure this guards against.
3. Select the catalytic STC copy **by distance to Ser64 OG**, not by file order.
   1L2S has three copies: A/1115 and B/2115 are catalytic (2.70 Å from Ser64
   OG); B/3115 sits at the chain interface, 22.7 Å from either active site.
   Chain A is missing Lys290–Ala292, so use chain B.
4. Derive the docking box from the ligand centroid with 8 Å padding.
5. Dock with Vina at **seed 42, exhaustiveness 32**.
6. Compute symmetry-corrected heavy-atom RMSD **without superposition**.
   Never `--minimize`; see the note below.
7. Emit `validation_record.md` in the format of Chapter 20's protocol record.

Three RMSD values from this script fill `[x]` placeholders in Chapter 17 of the
book. Report them when the script runs.

## `--minimize` must never be used

```bash
python -m spyrmsd ref.sdf pose.sdf              # correct
python -m spyrmsd --minimize ref.sdf pose.sdf   # WRONG — never
```

`--minimize` superimposes the two structures before measuring, which discards
exactly the thing a redock is testing. A pose displaced 3.0 Å returns `3.00000`
without the flag and `0.00000` with it. The flag makes every validation pass.
