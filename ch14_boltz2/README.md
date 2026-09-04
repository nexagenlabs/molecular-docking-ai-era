# Chapter 14 — boltz2

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch14_boltz2/run.sh
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

Boltz-2 on the FEP+ benchmark: **r = 0.62**, and therefore **r² = 0.38**,
against FEP+'s 0.52. The notebook must show the squaring step explicitly — the
book's argument turns on the difference between a correlation coefficient and
the variance it explains.
