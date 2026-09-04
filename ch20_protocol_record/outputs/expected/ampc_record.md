# Protocol record — 1L2S

Filled by `ch20_protocol_record/scripts/fill_record.py` on 2026-09-04 06:49 UTC
from `ch09_first_run/config/vina_config.txt` and `ch09_first_run/outputs/ampc/logs/modes.log`.

★ marks the tier-one fields: without them the run cannot be
re-executed, however complete the rest of the record is.

| Field | Value | Filled from |
|---|---|---|
| ★ Receptor source and identifier | RCSB `files.rcsb.org`, **1L2S**, 1.94 Å, R-free 0.207 | coordinate file header |
| Chains and altlocs kept | chain **B**; altlocs GLN B250 (first taken) | coordinate file |
| Waters and ions | 352 waters in the entry, all deleted; metals: **none** — AmpC is a class C serine hydrolase | coordinate file |
| Missing residues | chain A: LYS 290, ILE 291, ALA 292 | REMARK 465 |
| ★ Receptor preparation tool and version | meeko mk_prepare_receptor 0.8.0 | environment/resolved.txt |
| ★ Ligand source | ../outputs/ampc/ligand.pdbqt | config file |
| Ligand preparation | meeko mk_prepare_ligand 0.8.0 — from data/ligands/STC.sdf, formal charge -1 | config file |
| Stereochemistry as docked | **TODO(human)** — not derivable from a config file: state it yourself | — |
| ★ Box centre | 79.802, 5.352, 29.948 | config file |
| ★ Box dimensions | 23.74 × 20.60 × 23.18 | config file |
| Box derivation | centroid of B/2115 (2.70 Å from Ser64 OG), 8 Å padding | ligand copy selected by distance to Ser64 OG |
| ★ Docking program and version | AutoDock Vina v1.2.7 | run log |
| Exhaustiveness / num_modes / energy_range | 32 / 9 / 3 | config file |
| ★ Random seed | 42 | config file |
| Redocking result | best affinity -7.384 kcal/mol over 9 modes; RMSD to the crystal pose is NOT in this log | run log |
| Cross-docking or enrichment result | **TODO(human)** — a different experiment: fill from its own record | — |
| Exclusions and deviations | **TODO(human)** — the one field no tool can fill; it is why the record exists | — |

## What was not filled, and why

- **Stereochemistry as docked** — not derivable from a config file: state it yourself
- **Cross-docking or enrichment result** — a different experiment: fill from its own record
- **Exclusions and deviations** — the one field no tool can fill; it is why the record exists

Three fields need a human, and they are the three that matter most for
judging the work: what stereochemistry was actually docked, what other
experiment this belongs to, and what was excluded. **A tool can record
what happened. It cannot record what you decided.**

## Cross-checks against the coordinate file

| | |
|---|---|
| Resolution | 1.94 Å |
| R-free | 0.207 |
| Ligand copies found | 3 |
| Copy used | B/2115, 2.70 Å from Ser64 OG |
| Altlocs in the chain | GLN B250 |
| Metals | **none** |
| Covalent link to Ser64 | none |

The ligand copy is chosen by **distance to Ser64 OG**, never by file
order. This entry holds 3 copies and the one at 2.70 Å is the one
used; the others appear in the table above so the choice can be
checked rather than taken on trust.
