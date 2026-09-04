# Chapter 15 — the co-folding field

Published figures, with the columns that make them comparable.

## Run

```bash
bash ch15_cofolding_field/run.sh
```

## The table

| Method | Reported | Form | Variance explained | P(correct order) | Benchmark |
|---|---|---|---|---|---|
| Boltz-2 | 0.62 | **r** | 0.384 | 0.547 | FEP+ benchmark |
| FEP+ | 0.52 | **R²** | 0.520 | 0.562 | FEP+ benchmark |
| Vina (docking) | 0.90 | EF1% | — | — | LIT-PCBA |
| GNINA (rescoring) | 2.58 | EF1% | — | — | LIT-PCBA |

**The Form column is the one that matters.** The central failure in reading
this literature is comparing an r against an R².

## Two comparisons that go wrong

**Boltz-2 against FEP+.** *r = 0.62 against R² = 0.52* reads as ten points
ahead. Squared, it is **0.38 against 0.52** — fourteen points the other way.
Same two numbers, opposite conclusion, one keystroke apart.

**GNINA against Vina.** *2.58 against 0.90* reads as about three times better.
**Chance is 1.0**, so Vina is below it: one of those two methods is not
working, and the ratio hides which one.

## On this series

The AmpC series spans 0.32 kcal/mol. At the correlations above, ordering two of
its members correctly is 54.7% for Boltz-2 and 56.2% for FEP+, against 50.0%
for guessing.

This is not a ranking of methods. It is a demonstration that **the headline
numbers do not compare until you put them in the same form**, and that once you
do, the differences between the methods are smaller than the gap between all of
them and the question being asked.

## Assumption stated

P(correct order) assumes the population of compounds has a spread of
1.5 kcal/mol, which is typical for a congeneric series and is *wider* than this
one. A narrower population would make every figure worse, not better.
