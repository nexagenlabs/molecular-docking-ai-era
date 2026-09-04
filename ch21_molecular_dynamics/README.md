# Chapter 21 — molecular dynamics: every window looks converged

A synthetic RMSD trajectory built from four relaxation processes a decade
apart, observed through four windows also a decade apart. Each window is given
the test everyone actually applies: *has the second half stopped rising?*

## Run

```bash
bash ch21_molecular_dynamics/run.sh
```

**No MD software is required.** The trajectory is generated, not simulated —
deliberately, because the point is about how trajectories are *read*, and a
synthetic one is the only kind where the true answer is known. The GROMACS
pipeline is a separate matter.

## The result

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |
|---|---|---|---|---|
| 1 ns | 1.10 Å | +0.113 Å/ns | 1.53 Å | still rising |
| 10 ns | 1.42 Å | +0.015 Å/ns | 2.07 Å | looks converged |
| 100 ns | 1.80 Å | +0.004 Å/ns | 2.31 Å | looks converged |
| 1000 ns | 2.30 Å | +0.000 Å/ns | — | looks converged |

**Every window long enough that anyone would trust it passes**, and the 10 ns
answer is 38% below the 1000 ns one. Nothing available inside a 10 ns run says
so.

The flat-tail test is not bad because it is naive. It is bad because a process
slower than the window is invisible to it **by construction**: a trajectory
relaxing on a 100 ns timescale is perfectly flat across any 10 ns stretch of
itself. You cannot detect a timescale you did not sample.

## Against the book

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | −0.150 | +0.113 |
| 10 ns | 1.47 Å | 1.42 Å | −0.010 | +0.015 |
| 100 ns | 1.90 Å | 1.80 Å | +0.007 | +0.004 |
| 1000 ns | 2.34 Å | 2.30 Å | +0.0004 | +0.0000 |

The means land within 0.1 Å and the shortfall is 38% against the book's 37%,
so the chapter's argument reproduces. The slopes do not, and the reason is
worth stating precisely: **a monotone sum of exponentials cannot produce a
negative slope at all.** The book's −0.150 and −0.010 must come from the noise
in its trajectory, and the noise is a seed nobody wrote down.

Fitting amplitudes *and* timescales to all seven of the book's published
numbers leaves a residual around 0.08 Å that will not reduce further — which is
consistent with a noise realisation of the size the negative slopes imply. So
the deterministic half of the construction is recovered and the stochastic half
is not. See `PROGRESS.md`.

## Construction

- Four relaxation processes at **τ = 0.1, 1, 10, 100 ns**, one per observation
  window, so each window is ten times its own process.
- Amplitudes chosen so the window means land as close to the book's as a
  monotone four-exponential model reaches.
- Gaussian noise, **σ = 0.05 Å, seed 42**, sampled every 0.01 ns.
- "Looks converged" means the second-half slope is at most +0.02 Å/ns.

Every one of those is stated in the script as a named constant, because the
whole chapter is about what a number depends on.
