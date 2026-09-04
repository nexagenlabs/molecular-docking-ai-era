# Chapter 18 — enrichment

**Status: stub.** The directory exists so the path promised in the book
resolves; the script is not written yet.

## What this does

_To be written._

## Run

```bash
bash ch18_enrichment/run.sh
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

Two synthetic screens, 10,000 compounds, 100 actives, tuned to equal AUC:

| | AUC | EF1% | EF5% | BEDROC (α=20) |
|---|---|---|---|---|
| Screen A | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen B | 0.758 | 0.0 | 0.6 | 0.058 |

Identical AUC, opposite usefulness. BEDROC is cross-checked against
`rdkit.ML.Scoring.Scoring.CalcBEDROC` — the two agree to six decimals. At
α = 20, 79.8% of the weight falls in the top 8% of the ranked list.
