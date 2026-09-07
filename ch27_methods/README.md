# Chapter 27 — the methods section

A methods section written from memory a month after the run is a work of
fiction with a high hit rate. This one is generated from the protocol record.

## Run

```bash
bash ch27_methods/run.sh
```

## Depends on Chapters 20 and 17

Nothing in the generated text is computed here:

| Reads | Produced by |
|---|---|
| `ch20_protocol_record/outputs/filled_record.json` | `bash ch20_protocol_record/run.sh` |
| `ch17_validation/outputs/validation.json` | `bash ch17_validation/run.sh` |

Chapter 20 depends on Chapter 9 in turn, so the chain is ch09 → ch20 → ch27.
`run.sh` runs Chapter 20 first if the record is missing.

## What comes out

Six paragraphs in which every number is traceable to a file: the entry and its
resolution, the chain and why the other one was discarded, how the ligand copy
was selected and what the alternatives were, the box and its derivation, the
seed, and the RMSD with its definition attached.

Two sentences carry **[TODO]** markers:

| Field | Why a tool cannot fill it |
|---|---|
| Stereochemistry as docked | A config file records a filename, not what was in it |
| Exclusions and deviations | The one field no tool can fill; it is why the record exists |

**They are left visible in the paragraph itself**, not quietly omitted. A
methods section with a hole in it is one somebody will fix. One with a
plausible sentence covering the hole is one nobody will ever check — and that
is the failure this chapter is about, because at reading speed a fluent methods
section is indistinguishable from an accurate one.

## What the generated text gets right that memory usually does not

- The ligand copy was chosen by **distance to Ser64 OG**, and the discarded
  copy at 22.72 Å is named. A month later, nobody remembers there were three.
- The seed is stated **with the reason** — Vina's default of 0 selects a random
  seed, so a run at the default is not reproducible.
- The RMSD carries its definition: heavy-atom, symmetry-corrected, and computed
  **without superposition**, with a sentence saying what enabling superposition
  would have measured instead.
- The number of disordered side chains is counted from the coordinate file. In
  an earlier version of this script that count was produced by an expression
  that was nonsense and happened to return the right answer — which is exactly
  the kind of thing a generated methods section is supposed to make impossible,
  and it was caught by reading the code rather than the output.

None of those are hard to write down. They are hard to *remember* to write
down, which is a different problem and one a generator solves.
