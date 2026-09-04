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
