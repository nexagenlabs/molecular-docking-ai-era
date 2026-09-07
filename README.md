# Molecular Docking in the AI Era — companion repository

Code and data for *Molecular Docking in the AI Era* (Suryaprakash Tripathy,
NexaGenLabs).

The book makes quantitative claims. Every one is either computed from public
data or cited to a source. This repository lets you obtain the inputs and
reproduce the computed ones.

**The test it has to pass:** a stranger on a clean machine can clone it, run
one command per chapter, and get the numbers printed in the book.

## Install

```bash
git clone <this repo>
cd molecular-docking-ai-era

python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install openbabel         # 3.2.1 — confirm with obabel -V
```

The book's numbers were produced with **pip on Ubuntu, Python 3.12.3**.
`environment/environment.yml` exists for conda users and carries the same pins,
but conda-forge can resolve transitive dependencies differently — see
[`environment/README.md`](environment/README.md).

**Vina must report 1.2.7.** On Windows, `pip install vina` fails (the sdist
needs Boost and there is no wheel); use the official
`vina_1.2.7_win.exe` binary instead.

## Run

```bash
bash data/structures/fetch.sh      # 1L2S, 4JXS, 4JXV, 1GA9
python data/ligands/generate.py    # the three reference SDFs
bash ch09_first_run/run.sh         # the sample chapter
```

Every chapter directory holds a `README.md` saying what it does and what to
expect, a `run.sh` that goes from nothing to the result in one command, and
`outputs/expected/` with reference results — so you can tell whether your run
matched without opening the book.

```bash
pytest                             # 247 tests; every chapter has some
```

**It takes about half an hour**, because it is not checking files — it runs the
chapters. Nine of them dock, and Vina at exhaustiveness 32 is most of the wall
time. Each chapter runs once for the whole suite even where four test files
depend on it.

A test that asserted `run.sh` exits 0 would run in seconds and tell you
nothing, so these assert what each chapter claims instead: a value, a refusal,
the contents of a file, a selection made on the right grounds. Where a number
is docking output it is the *comparison* that is asserted — the AlphaFold pose
being worse than the crystal one, the undersized box being worse than both
larger ones — because the third decimal is platform-dependent and the
conclusion is not.

For a quick check while working, run one chapter:

```bash
pytest tests/test_ch14_boltz2.py   # a few seconds; pure arithmetic
pytest tests/test_gotchas.py       # the standing guards, no tools needed
```

## The running system

**AmpC β-lactamase from *Escherichia coli*** (UniProt P00811), a class C serine
hydrolase. **No catalytic metal** — the zinc enzymes are the class B
metallo-β-lactamases, a different protein. Three congeneric inhibitors sharing
an 18-heavy-atom core, spanning charges of −1 and −2 and affinities from 18 to
31 µM.

| Entry | Res. | Ligand | Role |
|---|---|---|---|
| 1L2S | 1.94 Å | STC | redocking target |
| 4JXS | 1.90 Å | 18U | cross-docking |
| 4JXV | 1.76 Å | 1MU | cross-docking |
| 1GA9 | 2.10 Å | ETP | **excluded** — covalent to Ser64 |

**Numbering trap: UniProt number = PDB number + 16.** Ser64 in the coordinate
files is Ser80 in UniProt and in the AlphaFold model. Chapter 6 shows what
happens otherwise: ask the model for residue 64 and it returns isoleucine, with
no error.

See [`data/structures/README.md`](data/structures/README.md) for the
per-structure details the scripts depend on, all measured from the files rather
than assumed.

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

## Three things that will silently ruin a result

1. **Never use `--minimize` when computing RMSD.** It superimposes before
   measuring, which discards the thing a redock tests. A pose displaced 3.0 Å
   returns `3.00000` without the flag and `0.00000` with it. `pytest` fails the
   build if the flag — or `minimize=True` — appears in any code here.
2. **Vina's default seed is 0, which means random.** Two runs at the default
   differ; two at seed 42 are byte-identical. Nothing in the log distinguishes
   them. Every run in this repository sets a seed, and `pytest` checks it.
3. **PDBQT loses formal charge and reorders atoms.** Round-tripping the 18U
   dianion returns the neutral diacid in a different atom order. Keep an SDF as
   the reference copy and convert outward only.

And one more this build discovered: **seed 42 is byte-identical within a build,
not across builds.** The same Vina 1.2.7 and RDKit 2026.3.5 give different
answers on Windows and Linux, for two measured reasons. See Chapter 9.

## Licence

**Code: MIT**, in [`LICENSE`](LICENSE) — the scripts and data-preparation code
only.

**The book's text and figures are not covered by it** and remain all rights
reserved. No figure images are committed here; each chapter's script draws its
own, so what you get is the figure regenerated from your run.

## Errata

Corrections to the book are collected in [`errata.md`](errata.md). Where this
repository disagrees with the book, both numbers are recorded in
[`PROGRESS.md`](PROGRESS.md) with a diagnosis, and neither is edited to match
the other.
