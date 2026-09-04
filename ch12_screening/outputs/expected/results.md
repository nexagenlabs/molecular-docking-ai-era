# Chapter 12 — screening

19 compounds into 1L2S chain B. AutoDock Vina v1.2.7, seed 42, exhaustiveness 8.

## The ranking

| Rank | Compound | MW | Affinity | |
|---|---|---|---|---|
| 1 | 18U | 339.4 | -8.090 | **known active** |
| 2 | 1MU | 353.4 | -8.033 | **known active** |
| 3 | furosemide | 330.7 | -7.826 |  |
| 4 | sulfamethoxazole | 253.3 | -7.771 |  |
| 5 | indomethacin | 357.8 | -7.603 |  |
| 6 | diclofenac | 296.2 | -7.410 |  |
| 7 | STC | 316.8 | -7.369 | **known active** |
| 8 | naproxen | 230.3 | -7.224 |  |
| 9 | warfarin | 308.3 | -7.222 |  |
| 10 | phenylbutazone | 308.4 | -6.963 |  |
| 11 | acetazolamide | 222.3 | -6.861 |  |
| 12 | probenecid | 285.4 | -6.731 |  |
| 13 | ibuprofen | 206.3 | -6.418 |  |
| 14 | aspirin | 180.2 | -6.233 |  |
| 15 | sulfanilamide | 172.2 | -5.850 |  |
| 16 | caffeine | 194.2 | -5.820 |  |
| 17 | salicylic_acid | 138.1 | -5.776 |  |
| 18 | benzoic_acid | 122.1 | -5.580 |  |
| 19 | paracetamol | 151.2 | -5.358 |  |

The three known actives rank 1, 2, 7 of 19.

## Enrichment is not defined at this size

The top 1% of 19 compounds is 0.19 compounds. **EF1% cannot be**
**computed here**, and any number reported for it would be an artefact
of rounding. Chapter 18 measures enrichment properly, on 10,000
compounds, and shows what the metric is and is not sensitive to.

The decoys here are also **not property-matched** to the actives — they
are common drugs, chosen so every SMILES is checkable against any
reference. A screen whose decoys are lighter and less charged than its
actives measures molecular weight, not binding.

## Failures

| Compound | Reason |
|---|---|
| sodium_chloride | meeko wrote no PDBQT |

Named, not skipped. A screen that quietly drops part of its library
reports an enrichment factor computed over a set nobody can
reconstruct — and the dropped rows are rarely a random sample of the
library.

## What it would cost

4.97 s per compound, measured on 4 cores.

| Library | Core-hours | Wall time on 100 cores |
|---|---|---|
| 10,000 | 55.2 | 0.02 days |
| 100,000 | 551.7 | 0.23 days |
| 1,000,000 | 5517.5 | 2.30 days |

Straight-line extrapolation, which assumes every compound costs what
these did. Bigger and more flexible ligands cost more, so this is a
floor rather than an estimate — and it is the number that decides
whether a screen happens, so it is worth measuring rather than guessing.
