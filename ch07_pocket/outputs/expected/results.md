# Chapter 7 — defining the pocket

Four box definitions, one protocol: AutoDock Vina v1.2.7, seed 42, exhaustiveness 32.

| Definition | Box (Å) | Volume (Å³) | Centre off by | Affinity | RMSD | Modes in site | Seconds |
|---|---|---|---|---|---|---|---|
| **ligand** | 23.7 × 20.6 × 23.2 | 11336 | 0.00 Å | -7.377 | 1.114 Å | 9/9 | 15.7 |
| **residues** | 31.8 × 34.5 × 37.6 | 41173 | 4.50 Å | -7.465 | 1.025 Å | 8/9 | 19.3 |
| **catalytic** | 22.0 × 22.0 × 22.0 | 10648 | 4.71 Å | -7.445 | 1.028 Å | 8/9 | 17.5 |
| **blind** | 60.0 × 60.8 × 51.4 | 187700 | 10.84 Å | -7.392 | 1.108 Å | 8/9 | 22.5 |

What each definition means:

- **ligand** — centroid of the crystallographic ligand, 8 A padding
- **residues** — centroid of 14 known site residues, 8 A padding
- **catalytic** — 22 A cube on Ser64 OG alone
- **blind** — the whole chain

The `ligand` row is the best case and is **not available in any real
project**: if you knew where the ligand sat you would not be docking.
It is here as the ceiling the others are measured against.
