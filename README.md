# Molecular Docking in the AI Era

Companion code for *Molecular Docking in the AI Era* by Suryaprakash Tripathy
(NexaGenLabs).

**The book is forthcoming.** This repository is published ahead of it, so the
chapter numbers refer to a text that is not out yet. The code runs and the
numbers reproduce on their own; you do not need the book to use it.

```bash
git clone https://github.com/nexagenlabs/molecular-docking-ai-era.git
cd molecular-docking-ai-era
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install openbabel          # 3.2.1 -- confirm with obabel -V
```

Windows needs two changes to that: `pip install vina` has no wheel and fails,
and Open Babel comes from pip instead. See
[`environment/README.md`](environment/README.md).

Then fetch the inputs and run the sample chapter:

```bash
bash data/structures/fetch.sh       # 1L2S, 4JXS, 4JXV, 1GA9
python data/ligands/generate.py     # the three reference SDFs
bash ch09_first_run/run.sh
```

Every chapter directory holds a `README.md`, a `run.sh` that goes from nothing
to the result in one command, and `outputs/expected/` with reference results —
so you can tell whether your run matched without opening the book.

## Chapters

| Chapter | What it does |
|---|---|
| [ch02_method_choice](ch02_method_choice/) | Method choice from the measurements, not from reputation — every row read out of another chapter |
| [ch03_databases](ch03_databases/) | Resolution and R-free by two routes; the R-free trap that is in both |
| [ch04_formats](ch04_formats/) | PDB and MOL2 are safe, PDBQT is not, and the folklore is out of date |
| [ch05_receptor_prep](ch05_receptor_prep/) | QC report for any entry: gaps, altlocs, bridging waters, covalent links |
| [ch06_predicted_structures](ch06_predicted_structures/) | A 0.216 Å backbone does not buy you a 1 Å pose |
| [ch07_pocket](ch07_pocket/) | Four ways to place the box, and what the choice costs here |
| [ch08_ligand_prep](ch08_ligand_prep/) | Protonation, stereochemistry, and conformer counts that do not track flexibility |
| [ch09_first_run](ch09_first_run/) | The seed, exhaustiveness, the box that fails silently, and mode 1's fake RMSD |
| [ch10_flexibility](ch10_flexibility/) | Three residues move; the other eleven do not |
| [ch11_web_servers](ch11_web_servers/) | 9 of 17 protocol fields survive a web server; the seed is not one |
| [ch12_screening](ch12_screening/) | A screen small enough to be honest about what it cannot measure |
| [ch13_cofolding](ch13_cofolding/) | The Boltz-2 input, frame-checked. The model needs a GPU |
| [ch14_boltz2](ch14_boltz2/) | r = 0.62 is r² = 0.38. One keystroke reverses the conclusion |
| [ch15_cofolding_field](ch15_cofolding_field/) | The field's headline numbers, in one form |
| [ch16_rescoring](ch16_rescoring/) | EF = 1.0 is chance, and Vina is below it |
| [ch17_validation](ch17_validation/) | The redock, and the flag that makes every validation pass |
| [ch18_enrichment](ch18_enrichment/) | Two screens, identical AUC, opposite usefulness |
| [ch20_protocol_record](ch20_protocol_record/) | Fourteen fields a machine can fill, and the three it cannot |
| [ch21_molecular_dynamics](ch21_molecular_dynamics/) | Every window looks converged |
| [ch22_free_energy](ch22_free_energy/) | Whether the calculation could answer the question, before running it |
| [ch23_interactions](ch23_interactions/) | 1.114 Å and 93% of the contacts are two different measurements |
| [ch24_network_pharmacology](ch24_network_pharmacology/) | The script that refuses to run without a background |
| [ch25_hit_to_bench](ch25_hit_to_bench/) | A docking score is not an affinity; designing the assay anyway |
| [ch26_case_study](ch26_case_study/) | Three reproduction tests, one of which fails informatively |
| [ch27_methods](ch27_methods/) | The methods section, generated from the record |

Chapters 1 and 19 have no code.

## Run the tests

```bash
pytest                              # 253 tests; every chapter has some
```

**It takes about half an hour**, because it runs the chapters rather than
checking that files exist. Nine of them dock, and Vina at exhaustiveness 32 is
most of the wall time. These assert what each chapter claims — a value, a
refusal, a selection made on the right grounds — not that `run.sh` exits 0.
Where a number is docking output it is the *comparison* that is asserted,
because the third decimal is platform-dependent and the conclusion is not.

## Versions

Six packages can move a published number and are pinned exactly: **vina 1.2.7**
(not 1.2.5, superseded February 2025), **rdkit 2026.3.5**, **spyrmsd 0.9.0**,
**meeko 0.8.0**, **numpy 2.4.4** and **Open Babel 3.2.1**. `requirements.txt`
is authoritative; `environment/environment.yml` carries the same pins for conda
users, but conda-forge can resolve transitive dependencies differently.

The book's numbers were produced with pip on **Ubuntu, Python 3.12.3**. Seed 42
is byte-identical within a build, not across builds: the same Vina and RDKit
give different third decimals on Windows and Linux, for two measured reasons.
See Chapter 9.

## Errata

Corrections to the book are collected in [`errata.md`](errata.md). Where this
repository disagrees with the book, both numbers are recorded with a diagnosis
and neither is edited to match the other.

## How this was built

[`build-record/`](build-record/) holds the plan, the defect reports and the
adversarial test of this repository against itself. None of it is needed to run
the code.

## Licence

**Code: MIT**, in [`LICENSE`](LICENSE) — the scripts and data-preparation code
only. **The book's text and figures are not covered by it** and remain all
rights reserved. No figure images are committed here; each chapter's script
draws its own.
