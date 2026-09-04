# Chapter 14 — Boltz-2

One keystroke reverses the conclusion.

## Run

```bash
bash ch14_boltz2/run.sh
```

## The squaring

| | Value |
|---|---|
| Boltz-2, reported **r** | 0.62 |
| Boltz-2, **r²** = 0.62 × 0.62 | **0.3844** |
| FEP+, reported **R²** | 0.52 |

**0.38 against 0.52.** Boltz-2 explains 38% of the variance in the FEP+
benchmark; FEP+ explains 52%.

Quoted as *"r = 0.62 against R² = 0.52"*, the newer method looks ahead by ten
points. It is behind by fourteen points of variance. An r and an R² are
different quantities, and putting them side by side is not a comparison — it is
the single most effective way to make a method look better than it is, and it
usually happens by accident rather than design.

The squaring is printed as `0.62 × 0.62 = 0.3844` rather than asserted, because
the book's argument depends on it and a reader should be able to watch it
happen.

## What r = 0.62 buys at the bench

Given two compounds whose true affinities differ by a known amount, how often
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
Φ(r·Δ / √(2(1−r²))). The two agree to three decimals — computed twice by
different routes, as everything in this repository that matters should be.

**The AmpC series in this repository spans 0.32 kcal/mol.** At that separation
a method with r = 0.62 gets the order right 54.8% of the time: 4.8 points
better than a coin flip.

That is not a criticism of Boltz-2. It is a statement about what *any* method
with that correlation can do, and about how tight a congeneric series has to be
before no method can help you. Chapter 26 arrives at the same place from the
other direction — by trying to rank the series and finding there is no reliable
ranking there to reproduce.
