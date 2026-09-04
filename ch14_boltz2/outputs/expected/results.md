# Chapter 14 — Boltz-2 and the squaring step

## Comparing like with like

| | Value |
|---|---|
| Boltz-2, reported **r** | 0.62 |
| Boltz-2, **r²** = 0.62 × 0.62 | **0.3844** |
| FEP+, reported **R²** | 0.52 |

**0.38 against 0.52.** Boltz-2 explains 38% of the variance in the
benchmark; FEP+ explains 52%.

Quoted as *r = 0.62 against R² = 0.52*, the newer method looks ahead. It
is not. An r and an R² are different quantities and a comparison between
them is not a comparison. The squaring is one keystroke and it reverses
the conclusion.

## What r = 0.62 buys

Two compounds whose true affinities differ by a known amount: how often
does a method with this correlation put them in the right order?

| True difference | P(correct order) | Better than a coin flip by |
|---|---|---|
| 0.32 kcal/mol | 0.548 | 4.8 points |
| 0.50 kcal/mol | 0.574 | 7.4 points |
| 1.00 kcal/mol | 0.645 | 14.5 points |
| 1.50 kcal/mol | 0.712 | 21.2 points |
| 2.00 kcal/mol | 0.772 | 27.2 points |
| 3.00 kcal/mol | 0.869 | 36.9 points |

Simulated over 400,000 pairs and checked against the closed form
Φ(r·Δ / √(2(1−r²))); the two agree to three decimals.

**The AmpC series in this repository spans 0.32 kcal/mol.** At that
separation a method with r = 0.62 gets the order right 54.8% of the
time — 4.8 points better than guessing.

That is not a criticism of Boltz-2. It is a statement about what *any*
method with that correlation can do, and about how tight a congeneric
series has to be before no method can help you. Chapter 26 reaches the
same conclusion from the other end, by trying to rank the series and
finding there is no reliable ranking there to reproduce.
