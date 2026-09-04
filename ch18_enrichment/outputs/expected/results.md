# Chapter 18 — enrichment

10000 compounds, 100 actives, α = 20, seed 42. Both screens are tuned to
the same AUC by solving for the active score mean; only the *spread* of
the active scores differs.

| | AUC | EF1% | EF5% | BEDROC (α=20) | Actives in top 1% |
|---|---|---|---|---|---|
| Screen A | 0.758 | 45.0 | 11.0 | 0.555 | 45 |
| Screen B | 0.758 | 0.0 | 0.8 | 0.059 | 0 |

**The same AUC, and one of these screens is useless.** Screen A puts 45
of its 100 actives in the first 1% of the list. Screen B puts 0 there.
Nobody screens the whole library, so AUC measures something nobody uses.

## BEDROC, computed twice

Once from Truchon & Bayly (2007) directly, once with
`rdkit.ML.Scoring.Scoring.CalcBEDROC`. They agree to six decimals:

| Screen | This implementation | RDKit |
|---|---|---|
| A | 0.55453405 | 0.55453405 |
| B | 0.05933767 | 0.05933767 |

At α = 20, **79.8% of BEDROC's weight falls in the top 8%** of the
list — analytic, so that figure is exact. α is not a tuning knob; it is
a statement about how much of the list you intend to look at.

## Against the book

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 45.0 | 11.0 | 0.555 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.8 | 0.059 |

The AUCs match because both are solved for. The rest depends on how the
screens were built, and `CLAUDE.md` records the book's results without
recording its construction — so these are two different synthetic
experiments that make the same point, not a disagreement about one.
See `PROGRESS.md`.
