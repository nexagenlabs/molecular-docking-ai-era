# Chapter 22 — free energy: can the question be answered?

Two independent estimates with standard error σ give a difference with
standard error σ√2, so resolving a difference Δ at 95% confidence needs

    σ < Δ / 2.77

## The series

| | Ki | ΔG |
|---|---|---|
| STC | 26.0 µM | -6.25 kcal/mol |
| 18U | 18.0 µM | -6.47 kcal/mol |
| 1MU_chembl | 26.0 µM | -6.25 kcal/mol |
| 1MU_pdbbind | 31.0 µM | -6.15 kcal/mol |

Full spread: **0.32 kcal/mol**.

## What each question needs

| Question | Δ | σ must be below |
|---|---|---|
| AmpC series, full spread (18-31 uM) | 0.32 kcal/mol | **0.116 kcal/mol** |
| a 2-fold difference in Ki | 0.41 kcal/mol | **0.148 kcal/mol** |
| a 10-fold difference in Ki | 1.36 kcal/mol | **0.492 kcal/mol** |
| a 100-fold difference in Ki | 2.73 kcal/mol | **0.984 kcal/mol** |

## Against what methods actually report

| Method | Statistical σ | Can resolve |
|---|---|---|
| well-converged FEP, one edge | 0.20 | a 10-fold difference in Ki; a 100-fold difference in Ki |
| typical production FEP | 0.35 | a 10-fold difference in Ki; a 100-fold difference in Ki |
| short FEP or small lambda ladder | 0.50 | a 100-fold difference in Ki |
| MM-GBSA (no formal error bar; typical spread) | 1.50 | **nothing above** |

Resolving the two ends of the AmpC series needs σ below **0.116**.
The best statistical error in the table is 0.20 — **2× too large**.

And that comparison flatters the method twice:

- It is the **statistical** error only: the uncertainty from finite
  sampling of a given force field. Force-field error is separate,
  larger, and does not shrink with more sampling.
- ChEMBL and PDBbind disagree about 1MU by **0.10 kcal/mol** — 32% of
  the entire spread being resolved. **The experimental answer is not
  known to the precision the calculation is being asked for.**

## The point

Not that free-energy methods are bad. They resolve a 10-fold difference
in Ki comfortably, and that is a question worth asking. The point is
that *this* series is the wrong experiment for them, and two lines of
arithmetic establish it before any compute is spent.

Chapter 14 reaches the same conclusion for a correlation-based method,
and Chapter 26 reaches it by trying the ranking and failing.

## No software was needed

No MD or FEP package is used here, and that is not a limitation of this
environment — the question is upstream of the calculation. Whether the
calculation *could* answer the question, if it ran perfectly, is decided
by the size of the effect and the precision of the method, both of which
are known before anything is submitted.
