# Chapter 23 — interaction fingerprints

An RMSD is one number for a whole molecule. It says the pose is 1.114 Å from
the crystallographic one. It does not say which contacts survived that
distance.

## Run

```bash
bash ch23_interactions/run.sh
```

Uses the poses from Chapter 17 and runs it first if they are missing.

## The result

**93% of the crystallographic interactions are reproduced** by a pose 1.114 Å
away.

| | Count |
|---|---|
| In both poses | 13 |
| In the crystal pose only — **missed** | 1 |
| In the docked pose only | 3 |

**Missed:** a hydrophobic contact with Ser64 at 3.51 Å — the catalytic
nucleophile.

**Invented:** a hydrogen bond to Gln120 at 2.94 Å, and edge-on aromatic
contacts with Tyr150 and Tyr221.

The Gln120 hydrogen bond is worth a second look. Chapter 10 identified Gln120
as one of only three binding-site residues that **change rotamer** across the
eight crystal chains. The docked pose is making a contact with a side chain
that is known to move, against a receptor held rigid in one of its
conformations. Whether that interaction is real depends on a degree of freedom
the calculation did not have.

## Why this is a separate measurement

RMSD and interaction recovery can disagree in both directions:

- A pose can sit **close** and miss the contact the chemistry depends on. Here
  it lost a contact with the catalytic serine while scoring 1.114 Å.
- A pose can sit **further away** and make every interaction, if the difference
  is a rotation of a symmetric group or a shift along an axis nothing touches.

If a redock is your only validation, you are measuring position and reporting
it as if it were chemistry.

## Cutoffs

| Interaction | Cutoff |
|---|---|
| Hydrophobic (C···C) | 4.5 Å |
| Hydrogen bond (heteroatom···heteroatom) | 3.5 Å |
| Salt bridge | 4.0 Å |
| Aromatic stacking (centroid···centroid) | 5.5 Å |
| Face-to-face if within | 30° of parallel |

Every one is a threshold on a continuum. A contact at 3.6 Å is not absent from
a 3.5 Å hydrogen-bond criterion — it is just outside it, and a fingerprint that
renders that as a clean 0 has invented precision the geometry does not have.

Detection is distance and angle only: no pharmacophore model, no scoring
function, nothing that could be tuned toward a nicer answer.
