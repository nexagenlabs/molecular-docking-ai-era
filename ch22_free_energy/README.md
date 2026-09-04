# Chapter 22 — free energy

Before running an alchemical calculation, ask what precision the question
needs. It is two lines of arithmetic and it is almost never done.

## Run

```bash
bash ch22_free_energy/run.sh
```

**No MD or FEP software is required, and none is used.** That is not a
limitation of this environment — the question is upstream of the calculation.
Whether a calculation *could* answer the question, if it ran perfectly, is
decided by the size of the effect and the precision of the method, and both are
known before anything is submitted.

## The arithmetic

Two independent estimates with standard error σ give a difference with standard
error σ√2, so resolving a difference Δ at 95% confidence needs

    σ < Δ / 2.77

| Question | Δ | σ must be below |
|---|---|---|
| AmpC series, full spread (18–31 µM) | 0.32 kcal/mol | **0.116** |
| a 2-fold difference in Ki | 0.41 kcal/mol | 0.148 |
| a 10-fold difference in Ki | 1.36 kcal/mol | 0.492 |
| a 100-fold difference in Ki | 2.73 kcal/mol | 0.984 |

| Method | Statistical σ | Can resolve |
|---|---|---|
| well-converged FEP, one edge | 0.20 | 10-fold, 100-fold |
| typical production FEP | 0.35 | 10-fold, 100-fold |
| short FEP or small λ ladder | 0.50 | 100-fold |
| MM-GBSA | ~1.50 | **nothing above** |

## The conclusion

Resolving the two ends of the AmpC series needs σ below **0.116 kcal/mol**. The
best statistical error in the table is 0.20.

That comparison flatters the method twice over:

- It is the **statistical** error only — the uncertainty from finite sampling of
  a given force field. Force-field error is separate, larger, and does not
  shrink with more sampling.
- ChEMBL and PDBbind disagree about 1MU by **0.10 kcal/mol**, which is 32% of
  the entire spread being resolved. **The experimental answer is not known to
  the precision the calculation is being asked for.**

The point is not that free-energy methods are bad. They resolve a 10-fold
difference in Ki comfortably, and that is a question worth asking. The point is
that **this series is the wrong experiment for them**, and two lines of
arithmetic establish it before any compute is spent.

Chapter 14 reaches the same conclusion for a correlation-based method. Chapter
26 reaches it by trying the ranking and failing. Three routes, one answer.
