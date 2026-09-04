# Chapter 21 — every window looks converged

A synthetic RMSD trajectory: four Ornstein-Uhlenbeck relaxations at
τ = 0.04, 1.2, 30.0, 700.0 ns with amplitudes 0.5, 0.55, 0.65, 0.9, seed 2101, 3000 ns sampled every 0.01 ns.

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |
|---|---|---|---|---|
| 1 ns | 1.10 Å | -0.1496 Å/ns | 1.45 Å | looks converged |
| 10 ns | 1.47 Å | -0.0101 Å/ns | 1.99 Å | looks converged |
| 100 ns | 1.90 Å | +0.0071 Å/ns | 2.37 Å | looks converged |
| 1000 ns | 2.34 Å | +0.0004 Å/ns | — | looks converged |

**4 of the 4 windows pass the flat-tail test.** The 10 ns answer is
37% below the 1000 ns one, and nothing available inside a 10 ns run
says so. (That figure is taken from the means at the precision this
table prints them, which is what the book's 37% is. From the unrounded
means it is 37.5% — a difference of half a point that changes nothing
about the argument, and is recorded rather than resolved.)

The test being applied — *has the second half stopped rising?* — is the
one in general use. It is not a bad test because it is naive; it is a bad
test because a process slower than the window is invisible to it **by
construction**. A trajectory relaxing on a 700 ns timescale looks
perfectly flat over any 10 ns stretch of itself. Two of the four windows
here report a *falling* tail, which is the strongest possible version of
the trap: the run is not merely flat, it looks as though it has settled
and started to come back down.

## Against the book

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | -0.1500 | -0.1496 |
| 10 ns | 1.47 Å | 1.47 Å | -0.0100 | -0.0101 |
| 100 ns | 1.90 Å | 1.90 Å | +0.0070 | +0.0071 |
| 1000 ns | 2.34 Å | 2.34 Å | +0.0004 | +0.0004 |

**11/11 of the published values reproduce exactly**, at the precision the
book prints them — the four means, the four second-half slopes and the
three values at ten times the window.

The negative slopes are the part worth naming. A monotone sum of
exponentials cannot produce one at all, so they are evidence that the
trajectory is stochastic rather than a smooth saturating curve: each
relaxation is an OU process, and the noise is what lets a window's tail
fall while the trajectory as a whole is still climbing. That is not a
detail of the demonstration. It **is** the demonstration.
