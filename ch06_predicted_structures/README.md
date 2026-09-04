# Chapter 6 — predicted structures

Can you dock into an AlphaFold model? The chapter answers it by docking into
one and measuring the pose, rather than by comparing backbones and hoping.

## Run

```bash
bash ch06_predicted_structures/run.sh
```

Fetches `AF-P00811-F1-model_v6.pdb` from the AlphaFold database; needs network
access the first time.

## 1. The numbering trap, demonstrated

**UniProt number = PDB number + 16** — recovered here from the sequences at
100% residue identity, not assumed.

| PDB | UniProt | Crystal | Model | Model at the PDB number |
|---|---|---|---|---|
| 64 | 80 | SER | SER | **ILE** |
| 67 | 83 | LYS | LYS | LYS |
| 119 | 135 | LEU | LEU | GLY |
| 120 | 136 | GLN | GLN | ILE |
| 150 | 166 | TYR | TYR | PHE |

Read the last column. Ask the model for residue 64 — the number the crystal
structure uses for the catalytic serine — and you get **isoleucine**. No error
is raised, nothing looks wrong, and everything downstream is about a different
residue. Note that residue 67 comes back as LYS either way, which is worse: a
spot check on that one residue would have passed.

## 2. Confidence where it matters

| | pLDDT |
|---|---|
| Whole chain | 96.4 |
| Binding site | 98.5 |

AlphaFold writes pLDDT into the B-factor column. This is an excellent model by
any measure — which is what makes the rest of the chapter interesting.

## 3. Geometry

| | RMSD |
|---|---|
| Whole-chain backbone (358 CA atoms) | **0.216 Å** |
| Binding-site CA | 0.241 Å |
| Binding-site side chains | 0.459 Å |

| Worst side chain | RMSD |
|---|---|
| Tyr221 | **1.72 Å** |
| Gln120 | 0.60 Å |
| Ala318 | 0.54 Å |
| Ser64 | 0.50 Å |

The backbone is essentially perfect. One side chain is not — and **Tyr221 is
one of the residues Chapter 10 measured as rigid**, varying by 10.6° across all
eight crystal chains. AlphaFold has put it somewhere no crystal structure puts
it, in a pocket it lines.

## 4. The test that settles it

| | RMSD to the crystal pose |
|---|---|
| Docked into the AlphaFold model | **3.140 Å** |
| Docked into the crystal structure (Chapter 17) | 1.114 Å |

Same ligand, same box, same seed, same exhaustiveness. The only difference is
the receptor. The best of the nine modes is 1.917 Å, so the right pose is
reachable — it is just not the one that scores best.

**A 0.216 Å backbone does not buy you a 1 Å pose.** Docking is a side-chain
problem, and a global confidence metric answers a question docking does not
ask. If you take one thing from this chapter, take the pair of numbers 0.216
and 3.140.

This is not an argument against predicted structures. It is an argument for
measuring the thing you actually care about: dock into the model, and check.
