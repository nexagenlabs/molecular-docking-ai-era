# CLAUDE.md

Project context for the companion repository to *Molecular Docking in the AI Era*
(Suryaprakash Tripathy, NexaGenLabs). Read this before doing anything.

---

## What this repository is

The book makes quantitative claims. Every one is either computed from public data
or cited to a source. This repository lets a reader obtain the inputs and
reproduce the computed ones.

**The success criterion: a stranger on a clean machine can clone this, run one
command per chapter, and get the numbers printed in the book.** A script that is
correct but unrunnable has failed.

Two rules follow.

- **Pin everything.** An unpinned environment means the reader's numbers differ
  from the book's and neither party knows why.
- **Ship expected outputs.** A reader must be able to tell whether their run
  matched without reading the book.

This repository is *reader-facing*. The book's own typesetting and figure-
generation pipeline lives elsewhere and is not part of this repo.

---

## Working style for this project

The book was written by verifying rather than asserting, and the repository
should be built the same way. Concretely:

- Run a command before documenting it.
- Compute a number twice by different routes where you can.
- When a primary source is unreachable and you read a mirror, say so.
- **Section 6 lists values the scripts must reproduce. If your script produces
  something different, do not adjust the script until it matches. Find out which
  side is wrong first.** That habit caught several real errors during writing,
  including one that would have made every validation test pass.

Ask before inventing. If a detail is not in this file and not obtainable from a
cited source, flag it rather than filling the gap plausibly.

---

## 1. The running system

**AmpC β-lactamase from *Escherichia coli*.** UniProt **P00811**. Class C serine
hydrolase — **no catalytic metal**. Do not apply zinc parameters; the zinc enzymes
are the class B metallo-β-lactamases and are a different protein.

### Structures

| Entry | Res. | R-free | Role | Critical detail |
|---|---|---|---|---|
| **1L2S** | 1.94 Å | 0.207 | Redocking target | Ligand **STC**, non-covalent. **Three copies**: A/1115 and B/2115 are catalytic (2.70 Å from Ser64 OG); B/3115 is at the chain interface, 22.7 Å from either active site — **discard it**. Chain A is missing Lys290–Ala292; **use chain B**. Sole altloc is Gln250. |
| **4JXS** | 1.90 Å | 0.212 | Cross-docking | Ligand **18U**. Inhibitor is in **chain B only** — chain A has phosphate and no ligand. Chain A missing 285–290. |
| **4JXV** | 1.76 Å | 0.232 | Cross-docking | Ligand **1MU**, present in **both chains**: A/402 is a single conformer, B/401 is modelled in **two altlocs**. Choosing a reference is therefore two decisions — chain, then conformer. No gaps, best resolution. |
| **1GA9** | 2.10 Å | 0.249 | **Excluded** | Ligand **ETP**, arylboronic acid, **covalent**: `LINK Ser64 OG — B`, 1.64 Å in chain A and 1.62 Å in chain B. Also carries a **K⁺ ion** from crystallisation — name it explicitly, because AmpC is a serine enzyme and a stray metal invites the misreading this book warns against. Non-covalent docking cannot represent this. The exclusion is a modelling decision and must be recorded as one. |

**Phosphates** in 4JXS, 4JXV and 1GA9 come from 1.7 M potassium phosphate
crystallisation. Nearest P to any Ser64 OG is **7.83 Å** (in 4JXS; the minimum across the three) — surface artefacts,
delete them. This was measured, not assumed.

**Bridging waters** in 1L2S chain B: HOH 403 (2.68 Å to the ligand carboxylate,
contacts Asn346 and Arg349) and HOH 481 (2.70 Å, contacts Thr316, Lys315,
Tyr150). Deleting them makes the crystallographic pose unreachable by docking.
Flag them; let the user decide.

**Numbering trap: UniProt number = PDB number + 16.** Ser64 in the coordinate
files is Ser80 in UniProt and in the AlphaFold model. Any script that mixes
UniProt annotations with PDB numbering will silently select the wrong residues.

### Binding-site residues (PDB numbering)

Ser64 (catalytic nucleophile), Lys67, Leu119, Gln120, Tyr150, Asn152, Tyr221,
Leu293, Lys315/Thr316/Gly317 (KTG motif), Ala318 (oxyanion hole), Asn346, Arg349.

Measured across eight chains: eight of these vary ≤20° in every torsion.
**Gln120, Leu293 and Thr316 change rotamer** — those are the only defensible
choices for flexible-residue docking.

### Ligand series

Congeneric, sharing an 18-heavy-atom core.

| Ligand | SMILES | Charge at pH 7.4 | Ki |
|---|---|---|---|
| **STC** | `c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)O)Cl` | **−1** | 26 µM |
| **18U** | `c1cc(ccc1CNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O` | **−2** | 18 µM |
| **1MU** | `c1cc(ccc1CCNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O` | **−2** | 26 µM (ChEMBL) / 31 µM (PDBbind) |

The 1MU value **disagrees between sources**. Report both; do not pick one.

Charges differ across the series — docking the drawn neutral forms gets every
member wrong by a different amount.

**Do not convert between Ki, IC50 and Kd.** ETP's 83 nM was measured with a
different substrate and buffer and is **not comparable** to the values above.

---

## 2. Directory structure

```
molecular-docking-ai-era/
  README.md
  CLAUDE.md
  LICENSE
  .gitignore
  environment/
    environment.yml          # fully pinned
  data/
    structures/fetch.sh      # download script, not the files
    ligands/                 # SDF reference copies
  chNN_<name>/
    README.md                # what this does, what to expect
    run.sh                   # one command, start to finish
    outputs/expected/        # reference results
  protocols/
    reproducibility_record.md
  errata.md
```

### Chapter directories (named in the book — a missing one is a broken promise)

`ch02_method_choice` `ch03_databases` `ch04_formats` `ch05_receptor_prep`
`ch06_predicted_structures` `ch07_pocket` `ch08_ligand_prep` `ch09_first_run`
`ch10_flexibility` `ch11_web_servers` `ch12_screening` `ch13_cofolding`
`ch14_boltz2` `ch15_cofolding_field` `ch16_rescoring` `ch17_validation`
`ch18_enrichment` `ch20_protocol_record` `ch21_molecular_dynamics`
`ch22_free_energy` `ch23_interactions` `ch24_network_pharmacology`
`ch25_hit_to_bench` `ch26_case_study` `ch27_methods`

(Chapters 1 and 19 have no code directory.)

---

## 3. Build order

Do **not** attempt everything at once. Build one chapter completely, get it
reviewed, then use it as the pattern.

1. Skeleton: directories, stub READMEs, `.gitignore`, `environment.yml`.
2. **`ch09_first_run` in full** — it is the sample chapter, its expected values
   are already measured, and it establishes the pattern.
3. `ch17_validation`, then `ch05_receptor_prep`, `ch08_ligand_prep`.
4. The rest.

---

## 4. Environment

```yaml
# pin exactly; these versions produced the book's numbers
vina=1.2.7          # NOT 1.2.5 — superseded February 2025
rdkit
spyrmsd
meeko
gemmi               # meeko needs it
openbabel
numpy
matplotlib
```

---

## 5. Three gotchas that must appear as code comments

**1. `--minimize` must never be used for RMSD.** It superimposes before
measuring, which discards the thing a redock tests. Tested: a pose displaced
3.0 Å returns `3.00000` without the flag and `0.00000` with it. The flag makes
every validation pass.

```bash
python -m spyrmsd ref.sdf pose.sdf        # correct
python -m spyrmsd --minimize ref.sdf pose.sdf   # WRONG — never
```

RMSD must be heavy-atom, symmetry-corrected, **no superposition**.

**2. Vina's default seed is 0, which means random.** Two runs at the default
differ; two at seed 42 are byte-identical. Nothing in the log distinguishes them.
Always set the seed explicitly and record it.

**3. PDBQT loses formal charge and reorders atoms.** Round-tripping the 18U
dianion returns the neutral diacid with a different atom order. The charge loss
matters because the series charges differ; the reordering matters because it
breaks any RMSD computed against the original ligand. Keep an SDF as the
reference copy and convert outward only.

---

## 6. Values the scripts must reproduce

Printed in the book. A mismatch means the script or the book is wrong — **find
out which before changing either.**

**ch04_formats** — Round-trip a charged ligand through each format and compare
canonical SMILES. PDB and MOL2 preserve charge, bond orders **and**
stereochemistry (Open Babel re-perceives from 3D; the folklore that PDB destroys
chemistry is out of date). **PDBQT returns the dianion neutral, atom order
changed.** XYZ loses charge.

**ch08_ligand_prep** — RDKit ETKDGv3, 300 attempts, `pruneRmsThresh=0.5`, seeds
1/7/42/99/2026:

| Ligand | Rot. bonds | Conformers by seed |
|---|---|---|
| STC | 4 | 17, 16, 15, 16, 15 |
| 18U | 6 | 10, 14, 9, 9, 9 |
| 1MU | 7 | 33, 39, 33, 30, 40 |

Counts do **not** track rotatable-bond count. That is the teaching point; do not
"fix" it.

**ch09_first_run** — Vina 1.2.7.

**These numbers come from a SYNTHETIC system, not from AmpC.** That was
deliberate: the measurements are cheap and anyone can repeat them in seconds.
Docking STC into AmpC gives entirely different scores and must not be compared
against them. Build the system with `scripts/make_test_system.py`:

```python
# ligand: N-methylbenzamide, 10 heavy atoms, explicit Hs kept in the SDF
m = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1C(=O)NC"))
AllChem.EmbedMolecule(m, randomSeed=11); AllChem.MMFFOptimizeMolecule(m)
Chem.MolToMolFile(m, "lig.sdf")          # explicit Hs — meeko requires them

# receptor: 140 carbons on a shell, radius 9.0–10.5 Å, centred on the origin
rng = np.random.default_rng(3)
for i in range(140):
    v = rng.normal(size=3); v /= np.linalg.norm(v)
    p = v * (9.0 + rng.uniform(0, 1.5))
    # ATOM record, element C, occupancy 1.00, B 0.00
```

Ligand prepared with meeko 0.8.0. Box centred at **(0, 0, 0)**, seed **42**,
exhaustiveness **8** for the box sweep, `cpu=4` for the timing run.

- seed 0 twice → different; seed 42 twice → byte-identical
- exhaustiveness 8 → 3.4 s; 32 → 14.2 s on 4 cores. **Absolute times are
  hardware-specific; assert only that the ratio is 3–5.**
- box 20/12/8 Å → **−4.905 / −4.911 / −2.748**, no error raised. Verified to
  three decimals on the environment in section 4.
- mode 1 always reports RMSD `0.000 0.000` — distance from mode 1, not from a
  crystal pose

The AmpC run is a *separate* part of this chapter and has no published expected
score. Keep the two clearly apart in `run.sh` and the README.

**ch10_flexibility** — Torsion analysis across the four structures, eight chains,
must return Gln120, Leu293 and Thr316 as the rotamer-changing residues.

**ch14_boltz2** — Boltz-2 FEP+ benchmark r = 0.62; **squared = 0.38** against
FEP+ 0.52. The notebook must show the squaring; the book's argument depends on it.

**ch16_rescoring** — GNINA LIT-PCBA median EF1% 1.88–2.58 against Vina 0.90.
**EF = 1.0 is chance**, so Vina is below it. Preserve that framing.

**ch18_enrichment** — Two synthetic screens, 10,000 compounds, 100 actives, tuned
to equal AUC **0.758**:

| | AUC | EF1% | EF5% | BEDROC(α=20) |
|---|---|---|---|---|
| Screen A | 0.758 | 56.0 | 11.6 | 0.574 |
| Screen B | 0.758 | 0.0 | 0.6 | 0.058 |

Cross-check BEDROC against `rdkit.ML.Scoring.Scoring.CalcBEDROC` — they agreed to
six decimals. At α = 20, 79.8% of the weight falls in the top 8% of the list.

**ch21_molecular_dynamics** — Synthetic trajectory, four separated relaxation
timescales:

| Window | Mean RMSD | Slope over 2nd half | Value at 10× window |
|---|---|---|---|
| 1 ns | 1.10 Å | −0.150 Å/ns | 1.45 Å |
| 10 ns | 1.47 Å | −0.010 | 1.99 Å |
| 100 ns | 1.90 Å | +0.007 | 2.37 Å |
| 1000 ns | 2.34 Å | +0.0004 | — |

Every window looks converged; the 10 ns answer is 37% below the 1000 ns one.

**ch26_case_study** — Three reproduction tests with published answers: redock
1L2S (original authors reported 1.75 and 1.87 Å against crystal), cross-dock into
4JXS and 4JXV, and rank the series against 26, 18 and 31 µM.

---

## 7. `ch17_validation` specification

The most load-bearing script. It must:

1. Fetch 1L2S, 4JXS, 4JXV from `files.rcsb.org`.
2. Separate receptor and ligand, and **print every HETATM group it did not use**
   — silent ligand mis-picking is the failure this guards against.
3. Select the catalytic STC copy by distance to Ser64 OG, not by file order.
4. Derive the box from the ligand centroid with 8 Å padding.
5. Dock with Vina at seed 42, exhaustiveness 32.
6. Compute symmetry-corrected heavy-atom RMSD **without superposition**.
7. Emit `validation_record.md` in the format of Chapter 20's protocol record.

Three RMSD values from this script fill `[x]` placeholders in the book's
Chapter 17. Report them when the script runs.

---

## 8. `.gitignore`

```
*.docx
*.pdf
__pycache__/
.ipynb_checkpoints/
validation_output/
data/structures/*.pdb
data/structures/*.cif
```

Structures are fetched, not committed.

---

## 9. Open decisions — ask, do not choose

1. Licence for the repository (book is commercial; code licence is separate).
2. Whether to ship the book's figures as images here, or link to the book.
3. Whether `data/ligands/` holds SDFs or a script that generates them from SMILES.
