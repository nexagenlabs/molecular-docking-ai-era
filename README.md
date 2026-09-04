# Molecular Docking in the AI Era — companion repository

Code and data for *Molecular Docking in the AI Era* (Suryaprakash Tripathy,
NexaGenLabs).

The book makes quantitative claims. Every one is either computed from public
data or cited to a source. This repository lets you obtain the inputs and
reproduce the computed ones.

**The test this repository has to pass:** a stranger on a clean machine can
clone it, run one command per chapter, and get the numbers printed in the book.

## Quick start

```bash
git clone <this repo>
cd molecular-docking-ai-era

python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install openbabel         # 3.2.1, a system binary -- confirm with obabel -V

bash data/structures/fetch.sh      # downloads 1L2S, 4JXS, 4JXV, 1GA9
bash ch09_first_run/run.sh         # the sample chapter
```

The book's numbers were produced with **pip on Ubuntu, Python 3.12.3**.
`environment/environment.yml` is there for conda users and carries the same
pins, but conda-forge can resolve transitive dependencies differently — see
[`environment/README.md`](environment/README.md).

Every chapter directory holds a `README.md` saying what it does and what to
expect, a `run.sh` that goes from nothing to the result in one command, and
`outputs/expected/` with reference results — so you can tell whether your run
matched without opening the book.

## The running system

**AmpC β-lactamase from *Escherichia coli*** (UniProt P00811), a class C serine
hydrolase. **No catalytic metal** — the zinc enzymes are the class B
metallo-β-lactamases, a different protein.

| Entry | Res. | Ligand | Role |
|---|---|---|---|
| 1L2S | 1.94 Å | STC | redocking target |
| 4JXS | 1.90 Å | 18U | cross-docking |
| 4JXV | 1.76 Å | 1MU | cross-docking |
| 1GA9 | 2.10 Å | ETP | **excluded** — covalent to Ser64 |

**Numbering trap: UniProt number = PDB number + 16.** Ser64 in the coordinate
files is Ser80 in UniProt and in the AlphaFold model. A script that mixes
UniProt annotations with PDB numbering selects the wrong residues silently.

See `data/structures/README.md` for the per-structure details that scripts here
depend on, all of them measured from the files rather than assumed.

## Three things that will silently ruin a result

1. **Never use `--minimize` when computing RMSD.** It superimposes before
   measuring, which discards the thing a redock tests. A pose displaced 3.0 Å
   returns `3.00000` without the flag and `0.00000` with it — the flag makes
   every validation pass. RMSD here is heavy-atom, symmetry-corrected, no
   superposition.
2. **Vina's default seed is 0, which means random.** Two runs at the default
   differ; two at seed 42 are byte-identical. Nothing in the log distinguishes
   them. Always set the seed and record it.
3. **PDBQT loses formal charge and reorders atoms.** Round-tripping the 18U
   dianion returns the neutral diacid in a different atom order. The charge loss
   matters because the series charges differ; the reordering breaks any RMSD
   computed against the original ligand. Keep an SDF as the reference copy and
   convert outward only.

## Status

Under construction. Chapter directories exist so the paths named in the book
resolve, but most hold stub scripts. `ch09_first_run` is the sample chapter and
lands first; `ch17_validation`, `ch05_receptor_prep` and `ch08_ligand_prep`
follow.

## Errata

Corrections to the book are collected in [`errata.md`](errata.md).

## Figures

No figure images are committed here. Each chapter's script draws its own plot
into its `outputs/` directory, so what you get is the figure regenerated from
your run rather than a copy of the book's. If yours differs from the printed
one, that is a result, not a rendering artefact.

## Licence

MIT, in [`LICENSE`](LICENSE) — the code and data-preparation scripts only. The
text and figures of the book are not covered by it.
