# Chapter 26 — case study

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch26_case_study/run.sh
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

Three reproduction tests, each against a published answer:

1. **Redock 1L2S** — the original authors reported 1.75 Å and 1.87 Å against the
   crystal pose.
2. **Cross-dock** into 4JXS and 4JXV.
3. **Rank the series** against Ki = 26 µM (STC), 18 µM (18U) and 31 µM (1MU).
   1MU's value disagrees between sources — ChEMBL gives 26 µM, PDBbind 31 µM.
   Report both; do not pick one.
