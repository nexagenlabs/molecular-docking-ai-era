# Chapter 6 — docking into a predicted structure

AlphaFold model of AmpC (UniProt P00811) against 1L2S chain B.

## 1. The numbering trap

**UniProt number = PDB number + 16**, recovered from the sequences here
rather than assumed, at 100.0% residue identity.

| PDB | UniProt | Crystal | Model | Model at the PDB number |
|---|---|---|---|---|
| 64 | 80 | SER | SER | ILE |
| 67 | 83 | LYS | LYS | LYS |
| 119 | 135 | LEU | LEU | GLY |
| 120 | 136 | GLN | GLN | ILE |
| 150 | 166 | TYR | TYR | PHE |
| 152 | 168 | ASN | ASN | GLN |
| 221 | 237 | TYR | TYR | GLU |
| 293 | 309 | LEU | LEU | PRO |
| 315 | 331 | LYS | LYS | LYS |
| 316 | 332 | THR | THR | ALA |
| 317 | 333 | GLY | GLY | ILE |
| 318 | 334 | ALA | ALA | THR |
| 346 | 362 | ASN | ASN | PRO |
| 349 | 365 | ARG | ARG | GLU |

Read the last column. Look up residue 64 in the model — the number the
crystal structure uses — and you get **ILE**, not the catalytic serine.
No error is raised. Everything downstream is about a different residue.

## 2. Confidence where it matters

| | pLDDT |
|---|---|
| Whole chain | 96.4 |
| Binding site | 98.5 |

AlphaFold writes pLDDT into the B-factor column. A whole-chain average
hides the only part docking uses: a model can average 90 and be useless
in the pocket.

## 3. Geometry

| | RMSD |
|---|---|
| Whole-chain backbone (358 CA atoms) | 0.216 Å |
| Binding-site CA | 0.241 Å |
| Binding-site side chains | 0.459 Å |

Worst side chains:

| Residue | RMSD |
|---|---|
| 221 | 1.72 Å |
| 120 | 0.60 Å |
| 318 | 0.54 Å |
| 64 | 0.50 Å |
| 349 | 0.46 Å |

## 4. The test that settles it

Backbone agreement is not the question. The question is whether a pose
docked into the prediction lands where the crystallographic one is.

| | RMSD to the crystal pose |
|---|---|
| Docked into the AlphaFold model | **3.140 Å** |
| Docked into the crystal structure (Chapter 17) | 1.114 Å |

Same ligand, same box, same seed, same exhaustiveness. The only
difference is the receptor.
