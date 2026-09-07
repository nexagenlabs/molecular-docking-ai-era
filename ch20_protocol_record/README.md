# Chapter 20 — the protocol record

Seventeen fields. Fourteen of them a machine can fill from the files a run
already left behind; three need a human, and those three are the ones that
matter most for judging the work.

## Run

```bash
bash ch20_protocol_record/run.sh
```

Or against your own run:

```bash
python ch20_protocol_record/scripts/fill_record.py \
    --config path/to/vina_config.txt --log path/to/vina.log \
    --structure 1L2S --chain B --ligand STC
```

## Depends on Chapter 9

The worked example is filled from two files ch09 leaves behind:

| Reads | Produced by | In a fresh clone |
|---|---|---|
| `ch09_first_run/config/vina_config.txt` | `derive_box.py`, PART 2.1 | **present** — it is committed |
| `ch09_first_run/outputs/ampc/logs/modes.log` | `modes.py --system ampc`, PART 2.2 | **absent** — gitignored |

The asymmetry in that last column is worth the space it takes. This script used
to stop with a clear message when the config was missing and carry on silently
when the log was — and the config is the one that cannot be missing. What the
silence produced was not an error but a plausible record: five TODOs instead of
three, no docking program, no redocking result, and nothing saying why. Both
inputs are now refused the same way, naming the file and the chapter.

`run.sh` checks for both and runs Chapter 9 if either is missing.

## What is here

| File | |
|---|---|
| `templates/blank_record.md` | The blank, with the tier-one fields marked |
| `scripts/fill_record.py` | Fills it from a config, a log and a coordinate file |
| `outputs/expected/ampc_record.md` | The worked AmpC example |

## The worked example

Filled from `ch09_first_run/config/vina_config.txt` and its run log:

| | |
|---|---|
| Receptor | **1L2S**, 1.94 Å, R-free **0.207** |
| Chain | **B** |
| Ligand copy | **STC B/2115**, 2.70 Å from Ser64 OG — chosen by distance, not file order |
| Altloc | **Gln250**, the entry's only one |
| Metals | **none** — AmpC is a class C serine hydrolase |
| Box centre | 79.802, 5.352, 29.948 |
| Seed | 42 |
| Program | AutoDock Vina v1.2.7 |

Fourteen fields filled, three left as `TODO(human)`.

## What a machine cannot fill

- **Stereochemistry as docked.** A config file records a filename, not what was
  in it.
- **Cross-docking or enrichment result.** A different experiment with its own
  record.
- **Exclusions and deviations.** The one field no tool can fill, and the reason
  the record exists. 1GA9 is the worked example: excluded because ETP is
  covalently bound to Ser64 OG, which is a modelling decision and has to be
  written down as one.

**A tool can record what happened. It cannot record what you decided.** Filling
the mechanical fields automatically is not a convenience — it is what makes the
three remaining gaps visible instead of buried in twenty lines of
transcription.

## The seed cross-check

The script compares the seed in the config against the seed in the log. If they
disagree, the config was edited after the run and the record describes a
protocol that was never executed — so it says so, loudly, rather than emitting
a tidy document. That check exists because a record which is merely tidy is
worse than none: it invites trust it has not earned.
