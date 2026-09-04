# Chapter 18 — enrichment

10000 compounds, 100 actives, α = 20, seed 2024. The two rankings are found
by searching for the pair that lands on the *same* AUC: 56 of screen A's
actives inside the top 1%, screen B's spread over ranks 401–4800. The two
AUCs differ by 1.63e-04.

| | AUC | EF1% | EF5% | BEDROC (α=20) | Actives in top 1% |
|---|---|---|---|---|---|
| Screen A | 0.758 | 56.0 | 11.6 | 0.574 | 56 |
| Screen B | 0.758 | 0.0 | 0.6 | 0.058 | 0 |

**The same AUC, and one of these screens is useless.** Screen A puts 56
of its 100 actives in the first 1% of the list. Screen B puts 0 there.
Nobody screens the whole library, so AUC measures something nobody uses.

## BEDROC, computed twice

Once from Truchon & Bayly (2007) directly, once with
`rdkit.ML.Scoring.Scoring.CalcBEDROC`. They agree to six decimals:

| Screen | This implementation | RDKit |
|---|---|---|
| A | 0.57380267 | 0.57380267 |
| B | 0.05777371 | 0.05777371 |

At α = 20, **79.8% of BEDROC's weight falls in the top 8%** of the
list — analytic, so that figure is exact. α is not a tuning knob; it is
a statement about how much of the list you intend to look at.

## Against the book

| | AUC | EF1% | EF5% | BEDROC |
|---|---|---|---|---|
| Screen A, book | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen A, here | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen B, book | 0.758 | 0.0 | 0.6 | 0.058 |
| Screen B, here | 0.758 | 0.0 | 0.6 | 0.058 |

**8/8 of the published values reproduce exactly**, at the precision the
book prints them. This is arithmetic on a fixed construction, so unlike
Chapters 8 and 9 there is no build-level difference to absorb: a reader
on any platform gets these numbers or has found a bug.
