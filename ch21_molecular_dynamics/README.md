# Chapter 21 — molecular dynamics: every window looks converged

A synthetic RMSD trajectory built from four relaxation processes at separated
timescales, observed through four windows also a decade apart. Each window is
given the test everyone actually applies: *has the second half stopped rising?*

## Run

```bash
bash ch21_molecular_dynamics/run.sh
```

Runs `scripts/ch21_make_trajectory.py` (the construction, which asserts its own
four window means) and then `scripts/convergence.py` (the analysis, report and
figure).

**No MD software is required.** The trajectory is generated, not simulated —
deliberately, because the point is about how trajectories are *read*, and a
synthetic one is the only kind where the true answer is known. The GROMACS
pipeline is a separate matter.

## The result

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |
|---|---|---|---|---|
| 1 ns | 1.10 Å | −0.1496 Å/ns | 1.45 Å | looks converged |
| 10 ns | 1.47 Å | −0.0101 Å/ns | 1.99 Å | looks converged |
| 100 ns | 1.90 Å | +0.0071 Å/ns | 2.37 Å | looks converged |
| 1000 ns | 2.34 Å | +0.0004 Å/ns | — | looks converged |

**Every window passes**, and the 10 ns answer is 37% below the 1000 ns one.
Nothing available inside a 10 ns run says so. (37% is the shortfall between the
means as this table prints them, which is what the book's figure is; from the
unrounded means it is 37.5%. Both are recorded in the output.)

Two of the four windows report a *falling* tail. That is the strongest form of
the trap: the run does not merely look flat, it looks as though it settled and
then started coming back down — while the trajectory as a whole is still
climbing towards an answer half an ångström higher.

The flat-tail test is not bad because it is naive. It is bad because a process
slower than the window is invisible to it **by construction**: a trajectory
relaxing on a 700 ns timescale is perfectly flat across any 10 ns stretch of
itself. You cannot detect a timescale you did not sample.

## Construction

- Four **Ornstein-Uhlenbeck** relaxations at **τ = 0.04, 1.2, 30 and 700 ns**,
  amplitudes 0.50, 0.55, 0.65 and 0.90 — the standard picture of a protein
  relaxing: fast side chains, then loops, then slower domain motion.
- Seed **2101**, 3000 ns sampled every 0.01 ns.
- The generator is consumed **once per process, in the order of `taus`**, so
  that order is part of the specification in the same way the seed is.
- "Looks converged" means the second-half slope is at most +0.02 Å/ns.
- The mean is taken over the window's second half; the value at 10× is averaged
  over the last 5% before that point rather than read off a single frame.

The noise is not decoration. A monotone sum of exponentials cannot produce a
negative slope at all, so the stochastic term is what makes the two shortest
windows look settled. Take it out and the demonstration weakens into an
argument about amplitudes.

Every one of those constants is a named value in `ch21_make_trajectory.py`,
imported by the analysis rather than restated, because the whole chapter is
about what a number depends on.

## Against the book

**All eleven published values reproduce exactly** — four means, four
second-half slopes and the three values at ten times the window:

| Window | Mean, book | Mean, here | Slope, book | Slope, here |
|---|---|---|---|---|
| 1 ns | 1.10 Å | 1.10 Å | −0.150 | −0.1496 |
| 10 ns | 1.47 Å | 1.47 Å | −0.010 | −0.0101 |
| 100 ns | 1.90 Å | 1.90 Å | +0.007 | +0.0071 |
| 1000 ns | 2.34 Å | 2.34 Å | +0.0004 | +0.0004 |

The script counts the agreement rather than asserting it, and prints any value
that did not match.
