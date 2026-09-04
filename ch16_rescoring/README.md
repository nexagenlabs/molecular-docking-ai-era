# Chapter 16 — rescoring

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch16_rescoring/run.sh
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

GNINA on LIT-PCBA: median EF1% **1.88–2.58**, against Vina's **0.90**.

**EF = 1.0 is chance.** Vina is below it. Keep that framing — quoting the two
numbers without it makes a below-chance result look merely worse.
