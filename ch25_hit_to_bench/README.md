# Chapter 25 — hit to bench

Turning a docking score into an experiment somebody can run.

## Run

```bash
bash ch25_hit_to_bench/run.sh
```

## A docking score is not an affinity

Vina reports kcal/mol, which invites conversion to a Ki. For this series that
gives:

| Ligand | Docking score | Ki if converted | Measured Ki | Out by |
|---|---|---|---|---|
| STC | −7.377 | 3.86 µM | 26 µM | 7× |
| 18U | −8.090 | 1.16 µM | 18 µM | 16× |
| 1MU | −7.916 | 1.55 µM | 26 µM | 17× |

Wrong by roughly an order of magnitude, in the same direction, for all three. A
Vina score is a ranking device on an energy-like scale. It is not a free energy
and it does not convert.

So the assay is designed around a **potency guess** — stated as a guess, and
wide enough to be wrong.

## The design

| | |
|---|---|
| Guess | 10 µM |
| Range | 0.1 – 1000 µM |
| Points | 13 (3 per decade) |
| Replicates | 3 |
| Well volume | 100 µL |
| Compound needed | **5.25 mg** |

All three measured Ki values fall inside the range, with room either side. The
guess was two decades low and the design still worked, **because the range is
four decades wide**. The cost of an extra decade is a few wells; the cost of
missing the curve is the whole experiment.

Compound quantity assumes a 10× stock and 5× the assay volume: enough to
pipette, and enough left when the first plate goes wrong. It is not a
theoretical minimum.

## What counts as confirmation

- A dose-response curve with a clear plateau at **both** ends.
- A Hill slope near 1. Far from 1 suggests aggregation, or a stoichiometry that
  is not 1:1.
- Activity that survives 0.01% detergent. **AmpC is a classic target for
  promiscuous aggregators** — a micromolar hit that vanishes with detergent was
  never a hit.
- The same answer from a second, orthogonal assay.

## What does not

- A single-concentration percentage inhibition.
- An IC50 compared against a Ki from another paper. IC50 depends on substrate
  concentration and Km; Ki does not. They are not interconvertible without
  both, and **no conversion between Ki, IC50 and Kd happens anywhere in this
  repository**.
