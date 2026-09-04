# Validation record

Emitted by `ch17_validation/scripts/validate.py` on 2026-09-04 05:46 UTC.
In the format of Chapter 20's protocol record; ★ marks the tier-one
fields, the ones whose absence stops re-execution.

## 1. Receptor

| Field | Value |
|---|---|
| ★ **Receptor source** | RCSB `files.rcsb.org`, entries 1L2S, 4JXS, 4JXV |
| Chains used | 1L2S chain B, 4JXS chain B, 4JXV chain A |
| Altlocs | default A throughout |
| Waters | all deleted |
| Ions and additives | all deleted; phosphates are crystallisation artefacts, nearest 7.83 Å from Ser64 OG |
| Missing residues | left as gaps; chain chosen to avoid them where possible |
| Disordered side chains | typed down to alanine where the file holds exactly alanine's heavy atoms |
| ★ **Receptor preparation tool** | meeko mk_prepare_receptor 0.8.0 |

Per entry:

- **1L2S**, chain B. Ligand copy B/2115 chosen by minimum distance to Ser64 OG (2.70 Å). 10 disordered side chains typed as alanine.
  - HETATM groups not used: HOH (352), STC (2)
- **4JXS**, chain B. Ligand copy B/401 chosen by minimum distance to Ser64 OG (2.55 Å). 11 disordered side chains typed as alanine.
  - HETATM groups not used: HOH (437), PO4 (2)
- **4JXV**, chain A. Ligand copy A/402 chosen by minimum distance to Ser64 OG (2.48 Å). 10 disordered side chains typed as alanine.
  - HETATM groups not used: 1MU (1), HOH (375), PO4 (1)

## 2. Ligand

| Field | Value |
|---|---|
| ★ **Ligand source** | `data/ligands/{STC,18U,1MU}.sdf`, generated from SMILES with explicit formal charges |
| Ligand preparation | meeko mk_prepare_ligand 0.8.0 |
| Protonation | pH 7.4: STC −1, 18U −2, 1MU −2 |
| Stereochemistry as docked | achiral; no stereocentres to preserve |

The docked ligand is a **generated** conformer, not the crystal pose.
Docking the crystal conformer back would test the search and nothing
else.

## 3. Search box

| Entry | ★ Box centre | ★ Box dimensions | Derivation |
|---|---|---|---|
| 1L2S | 79.802, 5.352, 29.948 | 23.74 × 20.60 × 23.18 | centroid of the crystallographic ligand, 8 Å padding |
| 4JXS | 80.973, 5.018, 31.199 | 23.75 × 20.81 × 26.74 | centroid of the crystallographic ligand, 8 Å padding |
| 4JXV | 24.398, 5.480, 13.041 | 21.74 × 20.93 × 28.60 | centroid of the crystallographic ligand, 8 Å padding |

## 4. Docking

| Field | Value |
|---|---|
| ★ **Program and version** | AutoDock Vina v1.2.7 |
| ★ **Random seed** | 42 |
| Exhaustiveness | 32 |
| num_modes / energy_range | Vina defaults (9 / 3) |
| Flexible residues | none; this is a rigid-receptor protocol |

## 5. Results

| Entry | Ligand | Best affinity | **RMSD to crystal pose** | Best over all modes |
|---|---|---|---|---|
| 1L2S | STC | -7.377 kcal/mol | **1.114 Å** | 1.114 Å (mode 1) |
| 4JXS | 18U | -7.805 kcal/mol | **2.999 Å** | 1.876 Å (mode 3) |
| 4JXV | 1MU | -8.131 kcal/mol | **10.526 Å** | 10.371 Å (mode 4) |

### How the RMSD was computed

| | |
|---|---|
| Tool | spyrmsd 0.9.0, `symmrmsd` |
| Heavy atoms only | yes |
| Symmetry-corrected | yes |
| **Superposition** | **no** — `minimize=False` |
| Reference pose | the crystallographic ligand, bond orders assigned from the reference SMILES |

`--minimize` superimposes before measuring and makes every redock pass:
a pose displaced 3.0 Å returns 3.00000 without it and 0.00000 with it.
A record that does not state superposition was off contains an RMSD
that means nothing.

## 6. Environment

| | |
|---|---|
| Platform | Windows-11-10.0.26200-SP0 |
| Python | 3.12.10 |
| Reference platform for exact values | no — see PROGRESS.md |
| Resolved packages | `environment/resolved.txt` |

## 6a. Sensitivity of the chain choice

| Entry | Protocol chain | RMSD | Alternative chain | RMSD | Difference |
|---|---|---|---|---|---|
| 4JXV | A | 10.526 Å | B | 4.609 Å | **5.917 Å** |

The chain was chosen on grounds that looked like tidiness — one
altloc decision rather than two. It moves the answer by more than
the 2 Å threshold the whole exercise is judged against. A
preparation decision is not cosmetic because the reasoning for it
sounded cosmetic.

## 7. Exclusions and deviations

- **1GA9 is excluded.** ETP is covalently bound to Ser64 OG (`LINK`,
  1.64 Å in chain A, 1.62 Å in chain B) and non-covalent docking cannot
  represent that bond. The exclusion is a modelling decision and is
  recorded as one, not left as a gap in the structure list.
- **4JXV uses chain A.** The ligand is present in both chains, but the
  chain B copy is modelled in two altlocs. Chain A is a single
  conformer, so it costs one decision rather than two. Arbitrary, and
  therefore recorded — and, as the sensitivity check below shows, not
  cosmetic.
- **All waters deleted**, including HOH 403 and 481 in 1L2S chain B,
  which bridge the ligand to the protein at 2.68 and 2.70 Å. This is the
  usual default and it can put the crystallographic pose out of reach.
