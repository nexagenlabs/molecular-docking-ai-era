# Structures

Fetched, not committed (see `.gitignore`):

```bash
bash data/structures/fetch.sh
```

SHA-256 of the files as downloaded from `files.rcsb.org` on 2026-09-04:

```
3f86cc280611a63fbcd80c7471b25839dff46753248ab6751d3ab41f83eed4c8  1L2S.pdb
8d3704bbde29b7d17447d5d193c82b8e068fb928db585356f18f5ddd35d46b2a  4JXS.pdb
0ecbc303b67d553b786469f27b32b2421ce867f16e9e65ca55d1c237420aa261  4JXV.pdb
87f66d8db89e8dfa949b79fed510d7d8ae3b8bbc4f43b4371a396a23a4902abe  1GA9.pdb
```

A different digest means RCSB has re-released the entry. That is not
necessarily a problem, but it means your numbers may differ from the book's for
a reason that has nothing to do with your protocol — record it.

## What each file contains

Everything below was measured from the coordinates, not assumed. The
measurements are reproduced by `scripts/audit_structures.py`.

### 1L2S — 1.94 Å, R-free 0.207 — redocking target

Ligand **STC**, non-covalent. **Three copies**, and the choice between them is
the whole point:

| Copy | Min. distance to Ser64 OG (chain A / chain B) |
|---|---|
| A/1115 | **2.70 Å** / 51.14 Å — catalytic |
| B/2115 | 51.23 Å / **2.70 Å** — catalytic |
| B/3115 | 22.72 Å / 23.38 Å — **chain interface, discard** |

Pick the copy by distance to Ser64 OG, never by file order.

Chain A is missing Lys290–Ala292 (REMARK 465), so **use chain B**. The sole
altloc in the entry is Gln250 in chain B.

**Bridging waters, chain B.** HOH 403 sits 2.68 Å from the ligand carboxylate
and contacts Asn346 and Arg349; HOH 481 sits 2.70 Å away and contacts Thr316,
Lys315 and Tyr150. Deleting them makes the crystallographic pose unreachable by
docking. Scripts here flag them and leave the decision to you.

### 4JXS — 1.90 Å, R-free 0.212 — cross-docking

Ligand **18U**, in **chain B only** — chain A has a phosphate and no inhibitor.
Chain A is missing Asn285–Lys290.

### 4JXV — 1.76 Å, R-free 0.232 — cross-docking

Ligand **1MU**. No missing residues, best resolution of the four. The ligand is
present in **both** chains: A/402 as a single copy (23 atoms, 2.48 Å from Ser64
OG) and B/401 in **two altlocs** (46 atoms in one residue). Pick one altloc —
and record which chain and which altloc, because both choices change the answer.

### 1GA9 — 2.10 Å, R-free 0.249 — excluded

Ligand **ETP**, an arylboronic acid, **covalently bound**:

```
LINK         OG  SER A  64                 B   ETP A 964     1555   1555  1.64
LINK         OG  SER B  64                 B   ETP B 964     1555   1555  1.62
```

Non-covalent docking cannot represent that bond, so 1GA9 is excluded from every
docking test here. **The exclusion is a modelling decision and is recorded as
one** — not a quiet omission. The entry is still fetched: Chapter 10's torsion
analysis uses all four structures, eight chains.

1GA9 also carries a K⁺ ion, coordinated by waters at the chain interface. It is
a crystallisation artefact. AmpC is a class C **serine** hydrolase with **no
catalytic metal**; the metal-dependent β-lactamases are the class B enzymes and
are a different protein.

## Phosphates

4JXS, 4JXV and 1GA9 were crystallised from 1.7 M potassium phosphate. Nearest
phosphorus to any Ser64 OG:

| Entry | Nearest P to Ser64 OG |
|---|---|
| 4JXS | 7.83 Å |
| 4JXV | 30.38 Å |
| 1GA9 | 25.17 Å |

All surface artefacts — delete them. Measured, not assumed.

## Binding-site residues (PDB numbering)

Ser64 (catalytic nucleophile), Lys67, Leu119, Gln120, Tyr150, Asn152, Tyr221,
Leu293, Lys315/Thr316/Gly317 (the KTG motif), Ala318 (oxyanion hole), Asn346,
Arg349.

Across eight chains, eight of these vary by ≤20° in every torsion. **Gln120,
Leu293 and Thr316 change rotamer** — the only defensible choices for
flexible-residue docking. See `ch10_flexibility/`.

**Numbering trap: UniProt number = PDB number + 16.** Ser64 here is Ser80 in
UniProt P00811 and in the AlphaFold model.
