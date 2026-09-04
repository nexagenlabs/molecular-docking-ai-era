# Chapter 18 — enrichment

Two virtual screens with the **same AUC** and opposite usefulness.

## Run

```bash
bash ch18_enrichment/run.sh
```

Runs `scripts/ch18_make_screens.py` (the construction, which asserts its own
result) and then `scripts/enrichment.py` (the measurement). Writes
`outputs/metrics.md`, `outputs/metrics.json` and `outputs/enrichment.png` — both
curves on one axis, because the point is that they coincide until you zoom into
the first 5%.

## The construction

10,000 compounds, 100 actives, one generator seeded at 2024. A nested search
walks `hi` from 40 to 69 (how many of screen A's actives sit in the top 1%) and
`lo` from 2000 to 6900 in steps of 100 (the upper rank bound of screen B's
spread), building both screens at every step and keeping the pair whose AUCs are
closest together. It lands on **hi = 56, lo = 4800**, with the two AUCs 1.6×10⁻⁴
apart.

**The generator is consumed sequentially across the whole search.** Every draw
in every rejected iteration moves the stream, so the loop bounds and their order
are as much a part of the specification as the seed is. Re-seeding inside the
loop, or narrowing a range, gives different screens with the same description.
That is why the construction lives in one file, is imported rather than copied,
and is run first by `run.sh`.

| Screen | How its actives are placed |
|---|---|
| A | 56 in the top 1% of the list, the remaining 44 anywhere below |
| B | all 100 spread over ranks 401–4800, none above rank 401 |

## What it shows

| | AUC | EF1% | EF5% | BEDROC (α=20) | Actives in top 1% |
|---|---|---|---|---|---|
| Screen A | 0.758 | 56.0 | 11.6 | 0.574 | 56 |
| Screen B | 0.758 | 0.0 | 0.6 | 0.058 | 0 |

Identical AUC. Screen A puts 56 of its 100 actives in the first 1% of the list;
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

**All eight published values reproduce exactly**, at the precision the book
prints them:

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.6 | 0.058 |

This is arithmetic on a fixed construction, so there is no build-level
difference to absorb the way there is in Chapters 8 and 9: a reader on any
platform gets these numbers or has found a bug. The script counts the
agreement rather than asserting it, and prints any value that did not match.
