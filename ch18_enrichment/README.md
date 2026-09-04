# Chapter 18 — enrichment

Two virtual screens with the **same AUC** and opposite usefulness.

## Run

```bash
bash ch18_enrichment/run.sh
```

Writes `outputs/metrics.md`, `outputs/metrics.json` and `outputs/enrichment.png`
— both curves on one axis, because the point is that they coincide until you
zoom into the first 5%.

## The construction

10,000 compounds, 100 actives. Decoys score from N(0, 1). Actives score from
N(μ, σ), and **only σ differs between the screens**:

| Screen | σ | What it represents |
|---|---|---|
| A | 3.0 | A long upper tail — a few actives score far above everything else |
| B | 0.45 | Every active scores slightly better than average, none outstandingly |

μ is then **solved by bisection** so that both screens land on AUC 0.758. That
is the experiment: hold AUC fixed, vary only where the actives sit.

## What it shows

| | AUC | EF1% | EF5% | BEDROC (α=20) | Actives in top 1% |
|---|---|---|---|---|---|
| Screen A | 0.758 | 45.0 | 11.0 | 0.555 | 45 |
| Screen B | 0.758 | 0.0 | 0.8 | 0.059 | 0 |

Identical AUC. Screen A puts 45 of its 100 actives in the first 1% of the list;
Screen B puts none there. **Nobody screens a whole library**, so AUC measures a
quantity nobody uses — it integrates over the 95% of the ranking you will never
look at.

## BEDROC, computed twice

Once implemented from Truchon & Bayly (2007) directly, once with
`rdkit.ML.Scoring.Scoring.CalcBEDROC`. The two agree to six decimals. Two
independent routes to the same number is worth more than one implementation
that looks right.

At α = 20, **79.8% of BEDROC's weight falls in the top 8%** of the list. That
is analytic — the weight is α·e^(−αx)/(1−e^(−α)) — so unlike everything else
here it is exact and platform-independent. α is not a tuning knob: it is a
statement about how much of the list you intend to look at.

## Against the book

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 45.0 | 11.0 | 0.555 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.8 | 0.059 |

The AUCs match because both are solved for. Screen B matches closely. Screen A
does not, and the reason is that **`CLAUDE.md` records the book's results
without recording its construction** — everything downstream of AUC depends on
exactly how the actives are arranged, and there are many arrangements with
AUC 0.758.

So these are two different synthetic experiments making the same point, not a
disagreement about one. The book's values are left in the test suite unchanged
and reported as XFAIL carrying both numbers. **Getting them to match would mean
reverse-engineering a construction from its results**, which would produce a
script that agrees with the book by design rather than by measurement — the
opposite of what this repository is for. See `PROGRESS.md`.
