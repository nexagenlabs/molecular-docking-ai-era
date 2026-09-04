# Chapter 21 — every window looks converged

A synthetic RMSD trajectory: four relaxation processes at τ = 0.1, 1.0, 10.0, 100.0 ns,
plus Gaussian noise (σ = 0.05 Å, seed 42).

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |
|---|---|---|---|---|
| 1 ns | 1.10 Å | +0.1126 Å/ns | 1.53 Å | still rising |
| 10 ns | 1.42 Å | +0.0149 Å/ns | 2.07 Å | looks converged |
| 100 ns | 1.80 Å | +0.0042 Å/ns | 2.31 Å | looks converged |
| 1000 ns | 2.30 Å | +0.0000 Å/ns | — | looks converged |

**3 of the 4 windows pass the flat-tail test**, including every window
long enough that anyone would trust it. The 10 ns answer is 38% below
the 1000 ns one, and nothing available inside a 10 ns run says so.

The test being applied — *has the second half stopped rising?* — is the
one in general use. It is not a bad test because it is naive; it is a bad
test because a process slower than the window is invisible to it **by
construction**. A trajectory relaxing on a 300 ns timescale looks
perfectly flat over any 10 ns stretch of itself.

## Against the book

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | -0.1500 | +0.1126 |
| 10 ns | 1.47 Å | 1.42 Å | -0.0100 | +0.0149 |
| 100 ns | 1.90 Å | 1.80 Å | +0.0070 | +0.0042 |
| 1000 ns | 2.34 Å | 2.30 Å | +0.0004 | +0.0000 |

The book's construction is not recorded — `CLAUDE.md` gives the results
and says the trajectory has four separated relaxation timescales. Fitting
amplitudes *and* timescales to the book's seven published numbers leaves
a residual of about 0.08 Å that will not reduce, which is itself
informative: a monotone sum of exponentials cannot produce the reported
**negative** slopes at all. Those need noise, and the noise realisation
is a seed nobody wrote down.

So the deterministic half is reconstructed and the stochastic half is
not. What reproduces is every qualitative claim, including the one the
chapter is about: the shortfall between the 10 ns and 1000 ns answers is
38% here against the book's 37%.
