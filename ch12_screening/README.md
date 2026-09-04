# Chapter 12 — screening

Twenty compounds into AmpC: the three known actives plus seventeen common
drugs. Twenty is far too few to measure enrichment, and saying so precisely is
part of the chapter.

## Run

```bash
bash ch12_screening/run.sh
```

## What twenty compounds can and cannot tell you

**Cannot: enrichment.** The top 1% of nineteen compounds is 0.19 compounds.
EF1% is not defined here and any number reported for it would be an artefact of
rounding. Chapter 18 measures enrichment properly, on 10,000.

**Can: the parts of a screen that break at scale.**

## The failure

| Compound | Reason |
|---|---|
| sodium_chloride | meeko wrote no PDBQT |

Sodium chloride is in the library on purpose. Real vendor catalogues contain
salts, mixtures and rows with no organic ligand at all, and a screen has to
survive them. This one is **named and counted**, not skipped — a pipeline that
quietly drops part of its library reports an enrichment factor computed over a
set nobody can reconstruct, and the dropped rows are rarely a random sample.

## The ranking

The three known actives rank **1, 2 and 7** of 19.

18U and 1MU come first. **STC — a genuine 26 µM binder — is seventh**, behind
furosemide, sulfamethoxazole, indomethacin and diclofenac.

That is not a malfunction. Those four are acidic sulfonamides and carboxylic
acids: chemically they look like the actives, because the actives are acidic
sulfonamides too. A decoy set drawn from the same chemical space as the actives
is a *hard* decoy set, and hard decoy sets are the only kind that measure
anything. The corollary is uncomfortable and worth stating: on this evidence,
docking cannot separate the known AmpC binders from four ordinary drugs.

**The decoys are not property-matched**, which is a real weakness. They were
chosen so that every SMILES is checkable against any reference. A screen whose
decoys are lighter and less charged than its actives measures molecular weight
rather than binding — and would have flattered this result rather than
puncturing it.

## What it would cost

5.29 s per compound, measured on 4 cores.

| Library | Core-hours | Wall time on 100 cores |
|---|---|---|
| 10,000 | 58.7 | 0.02 days |
| 100,000 | 587.5 | 0.24 days |
| 1,000,000 | 5,874.9 | 2.45 days |

Straight-line extrapolation, which assumes every compound costs what these did.
Bigger and more flexible ligands cost more, so this is a **floor** rather than
an estimate. It is also the number that decides whether a screen happens, which
is why it is worth measuring rather than guessing.
