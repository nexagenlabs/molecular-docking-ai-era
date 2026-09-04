# Chapter 23 — interaction fingerprints

The crystallographic pose of STC in 1L2S chain B, against the pose docked
in Chapter 17 — which is **1.114 Å** away by symmetry-corrected RMSD.

| Residue | Crystal pose | Docked pose | |
|---|---|---|---|
| Ser64 | hbond 2.70 Å, hydrophobic 3.51 Å | hbond 2.80 Å | **missed** |
| Lys67 | hbond 3.12 Å | hbond 3.20 Å | same |
| Leu119 | hydrophobic 3.95 Å | hydrophobic 3.41 Å | same |
| Gln120 | — | hbond 2.94 Å | extra |
| Tyr150 | hydrophobic 4.22 Å | hydrophobic 3.84 Å, pi_edge 5.46 Å | extra |
| Asn152 | hbond 2.72 Å | hbond 2.95 Å | same |
| Val211 | hydrophobic 4.48 Å | hydrophobic 3.65 Å | same |
| Tyr221 | hydrophobic 4.20 Å | hydrophobic 3.71 Å, pi_edge 5.08 Å | extra |
| Leu293 | hydrophobic 3.96 Å | hydrophobic 3.47 Å | same |
| Gly317 | hydrophobic 4.04 Å | hydrophobic 4.49 Å | same |
| Ala318 | hbond 2.67 Å, hydrophobic 3.81 Å | hbond 2.91 Å, hydrophobic 3.91 Å | same |
| Thr319 | hydrophobic 3.62 Å | hydrophobic 3.72 Å | same |
| Gly320 | hydrophobic 4.26 Å | hydrophobic 4.47 Å | same |

**93% of the crystallographic interactions are reproduced.**

| | Count |
|---|---|
| In both | 13 |
| In the crystal pose only (missed) | 1 |
| In the docked pose only | 3 |

An RMSD is one number for a whole molecule. It says the pose is 1.114 Å
away; it does not say which contacts survived that distance. The two
measurements can disagree in both directions — a pose can sit close and
miss the interaction the chemistry depends on, or sit further away and
make every one of them.

## Cutoffs

| Interaction | Cutoff |
|---|---|
| Hydrophobic (C···C) | 4.5 Å |
| Hydrogen bond (heteroatom···heteroatom) | 3.5 Å |
| Salt bridge | 4.0 Å |
| Aromatic stacking (centroid···centroid) | 5.5 Å |
| Face-to-face, if within | 30° of parallel |

Every one is a threshold on a continuum. A contact at 3.6 Å is not
absent from a 3.5 Å hydrogen-bond criterion — it is just outside it, and
a fingerprint that renders that as a clean 0 has invented precision the
geometry does not have. Detection here is distance and angle only: no
pharmacophore model and no scoring function, so there is nothing to tune
toward a nicer answer.
