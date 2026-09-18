# dock.nexagenlabs.com — site content

Draft content for the companion site, in the voice of `lab.nexagenlabs.com`.
Five pages plus a `_redirects` file. Deploys to Netlify.

The repository is live at
`https://github.com/nexagenlabs/molecular-docking-ai-era`. Verify paths against
it before writing links.

---

## `/` — the hub

```markdown
# Molecular Docking in the AI Era

Companion code for *Molecular Docking in the AI Era: A Hands-On Handbook for
Structure-Based Drug Discovery*, by Suryaprakash Tripathy.

Twenty-five chapters ship code, one folder each, in
[one repository](https://github.com/nexagenlabs/molecular-docking-ai-era).
Clone it once and you have everything in the book. Each chapter stands alone:
open its folder, run `run.sh`, and the numbers printed in that chapter come out.

**Start here.** Setup, the pinned environment, and the structures the book
uses: [`dock.nexagenlabs.com/setup`](https://dock.nexagenlabs.com/setup)

## Every number in the book is asserted by a test

The book prints measured values rather than illustrative ones. Those values
live in the repository as expected results, and the test suite asserts them, so
a divergence between page and code shows up as a failing build rather than as a
reader's afternoon.

Two hundred and fifty-three tests pass, on Windows and on Ubuntu, from a fresh
clone. A few are marked expected-to-fail where different RDKit and AutoDock Vina
builds produce slightly different coordinates; the reasons are attached to each.
Nothing is tuned to match.

## Three things that silently ruin a result

`--minimize` on an RMSD call superimposes before measuring, so every redock
passes. Vina's default seed of 0 means random, not zero, so an unseeded run
cannot be repeated. And PDBQT drops formal charge and reorders atoms, so keep an
SDF as the reference copy. None of the three produces an error.

## One system, all the way through

Every chapter from 5 onward uses **AmpC β-lactamase from *Escherichia coli***
(UniProt P00811): four public crystal structures, a congeneric series of
inhibitors with measured affinities, and five published prospective screening
campaigns with experimental follow-up. Everything that can be reproduced from
public files, can be.

## The chapters

| Chapter | What the code does | Address |
| --- | --- | --- |
| 2 | Cost comparison across docking, co-folding and free energy methods | `/ch02` |
| 3 | Provenance recorder, and a check for whether your target is in PDBbind | `/ch03` |
| 4 | Format round-trips, measured. What PDBQT loses and PDB does not | `/ch04` |
| 5 | Receptor QC: gaps, altlocs, ligand copies, bridging waters, buffer | `/ch05` |
| 6 | Per-residue confidence for a predicted structure's binding site | `/ch06` |
| 7 | Box definition from a reference ligand, with the derivation recorded | `/ch07` |
| 8 | Protonation, stereochemistry round-trip, conformer generation | `/ch08` |
| 9 | A reproducible run: the seed, the box, and what silence looks like | `/ch09` |
| 10 | Side-chain torsions across structures: which residues actually move | `/ch10` |
| 11 | Turning a server result into something a protocol record can hold | `/ch11` |
| 12 | Parallel screening with checkpointing, and the filter cascade | `/ch12` |
| 13 | Co-folding submission and confidence parsing for the binding site | `/ch13` |
| 14 | Affinity prediction, and the squared-correlation diagnostic | `/ch14` |
| 15 | Running two co-folding models and reporting where they disagree | `/ch15` |
| 16 | Rescoring, and a check for training-set overlap with your target | `/ch16` |
| 17 | Redocking and cross-docking, with symmetry-corrected RMSD | `/ch17` |
| 18 | Two screens with identical AUC and opposite early enrichment | `/ch18` |
| 20 | The protocol record, blank and filled, populated from a run log | `/ch20` |
| 21 | Why a flat RMSD trace is not a converged one | `/ch21` |
| 22 | Free energy with replicates, and standard errors that mean something | `/ch22` |
| 23 | Interaction geometry alongside interaction names | `/ch23` |
| 24 | Enrichment that refuses to run without an explicit background | `/ch24` |
| 25 | Dose-response fitting that reports the Hill slope beside the IC50 | `/ch25` |
| 26 | Three reproduction tests with published answers | `/ch26` |
| 27 | Methods paragraphs drafted from a protocol record | `/ch27` |

Chapters 1 and 19 ship no code, so there is no `/ch01` or `/ch19`. If you typed
one, you are in the right place already.

## Versions

Parts of this book date faster than the rest. Model releases, licences and tool
versions are listed with a dated changelog at
[`dock.nexagenlabs.com/versions`](https://dock.nexagenlabs.com/versions).
Chapters 13 to 16 point here for a reason.

## References

The reference list as machine-readable data, with a DOI on every entry that has
one: [`dock.nexagenlabs.com/references`](https://dock.nexagenlabs.com/references)

## Errata

Corrections to the printed book are listed on the
[errata page](https://dock.nexagenlabs.com/errata). If you have found an error
in the book or the code, please report it: the page says how.

Code is MIT licensed. Book text and figures are not.
```

---

## `/setup`

```markdown
# Setup

[Back to the hub](https://dock.nexagenlabs.com/).

Everything in this book runs on free software. One environment covers every
chapter except the three noted at the bottom.

## Clone and install

    git clone https://github.com/nexagenlabs/molecular-docking-ai-era.git
    cd molecular-docking-ai-era
    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

Python 3.12 specifically. The pinned RDKit does not resolve on 3.14. The
repository's `environment/README.md` carries the exact per-platform recipe,
including the AutoDock Vina binary, which pip does not provide on every
platform.

## Check it worked

    bash ch09_first_run/run.sh

That is the sample chapter. It docks a small synthetic system, demonstrates that
the default seed is not reproducible and a fixed one is, and prints three
box-size results. Those three numbers are in Chapter 9. If they match, your
environment is correct.

## The structures

The book uses four PDB entries: 1L2S, 4JXS, 4JXV and 1GA9. They are downloaded
rather than committed, so that you get them from the source:

    bash data/structures/fetch.sh

Checksums are in `data/structures/README.md`.

## Why the versions are pinned exactly

Six packages can change a number printed in the book: RDKit, AutoDock Vina,
spyrmsd, Meeko, NumPy and Open Babel. They are pinned exactly. Matplotlib and
SciPy affect only plots and carry minimum bounds.

If your numbers differ from the book's, that is information rather than a fault.
The build record in the repository lists the differences already found, and what
caused them.

## What does not run everywhere

Three chapters need software that may not install on your machine: GNINA
(Chapter 16), Boltz-2 (Chapter 14) and PDBFixer (Chapters 5 and 6). Each
pipeline is written and each exits with the exact command it would have run, so
you can see what was intended without installing anything.

**Do not install Boltz-2 into this environment.** It succeeds and silently
downgrades NumPy, gemmi and SciPy, which changes the conformer counts in
Chapter 8 and the RMSD values in Chapter 17. Use a separate environment.

Code is MIT licensed. Book text and figures are not.
```

---

## `/versions`

```markdown
# Versions

[Back to the hub](https://dock.nexagenlabs.com/).

Part IV of this book covers software that changes faster than a book can be
reprinted. This page carries the current state and a dated record of what has
moved, so that a chapter written in 2026 stays usable.

Where this page and the printed book disagree, this page is current and the book
records what was true when it was checked.

## Tools

| Tool | Version in the book | Current | Checked |
| --- | --- | --- | --- |
| AutoDock Vina | 1.2.7 | | |
| smina | | | |
| RDKit | 2026.3.5 | | |
| Open Babel | 3.2.1 pinned; 3.1.x is what installs | | |
| spyrmsd | 0.9.0 | | |
| Meeko | 0.8.0 | | |
| GNINA | | | |
| PLIP | | | |
| GROMACS | | | |

## Models and their terms

| Model | Licence in the book | Current | Checked |
| --- | --- | --- | --- |
| AlphaFold 3 code | CC BY-NC-SA 4.0 | | |
| AlphaFold 3 weights | By request, non-commercial organisations only | | |
| Boltz-2 | MIT | | |
| Chai-1 | Apache 2.0 | | |
| Protenix | Apache 2.0 | | |

Chapter 13 states that AlphaFold 3's weights are restricted by organisation type
rather than by activity. Chapter 14 reports Boltz-2 benchmarks that predate
Boltz-2.1. Chapter 15 says explicitly that something will have been released
between writing and reading.

## Changelog

| Date | What changed | Affects |
| --- | --- | --- |

Code is MIT licensed. Book text and figures are not.
```

---

## `/errata`

Follow the structure and wording of `lab.nexagenlabs.com/errata`, with the
repository link pointing at `nexagenlabs/molecular-docking-ai-era`, and the code
section rewritten as:

```markdown
## Code corrections

Where a correction affects code rather than prose, the repository is fixed as
well, and the commit is the record. Every measured value the book prints is
asserted by a test in the repository, so a divergence between page and code
shows up as a failing build rather than as a reader's afternoon.
```

---

## `/references`

Stub for now. Follow `lab.nexagenlabs.com/references` when the book's reference
list exists: machine-readable, DOI on every entry that has one, verification
status per entry.

---

## `_redirects`

25 routes, 302 rather than 301 so a destination can be changed after printing.
Verify every target against the live repository before deploying.

```
/ch02   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch02_method_choice           302
/ch03   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch03_databases               302
/ch04   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch04_formats                 302
/ch05   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch05_receptor_prep           302
/ch06   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch06_predicted_structures    302
/ch07   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch07_pocket                  302
/ch08   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch08_ligand_prep             302
/ch09   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch09_first_run               302
/ch10   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch10_flexibility             302
/ch11   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch11_web_servers             302
/ch12   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch12_screening               302
/ch13   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch13_cofolding               302
/ch14   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch14_boltz2                  302
/ch15   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch15_cofolding_field         302
/ch16   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch16_rescoring               302
/ch17   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch17_validation              302
/ch18   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch18_enrichment              302
/ch20   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch20_protocol_record         302
/ch21   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch21_molecular_dynamics      302
/ch22   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch22_free_energy             302
/ch23   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch23_interactions            302
/ch24   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch24_network_pharmacology    302
/ch25   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch25_hit_to_bench            302
/ch26   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch26_case_study              302
/ch27   https://github.com/nexagenlabs/molecular-docking-ai-era/tree/main/ch27_methods                 302
```

`/ch01` and `/ch19` are deliberately absent. The 404 page should say so and link
to the hub.

---

## Open questions

1. **Redirect or landing page per chapter?** The redirects above send readers
   straight to GitHub. A landing page per chapter would let you attach chapter
   errata and a note when something is superseded, which matters most for
   Chapters 13 to 16. More work; better for a book with a long shelf life.
2. **Addresses in the book, or QR codes?** `lab.nexagenlabs.com` prints
   addresses inline. For a book read at a desk beside a laptop, a typeable short
   address is arguably better than a code needing a phone.
