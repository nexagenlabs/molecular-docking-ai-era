# Protocol record — template

> **Draft.** The fields below are the ones the scripts in this repository can
> fill and a reader needs in order to tell why their numbers differ from yours.
> The layout still has to be checked against Chapter 20 of the book, which is
> the authority on the format. `ch17_validation` emits `validation_record.md`
> in this shape.

Copy this file, fill every field, and keep it with the results it describes. A
field you cannot fill is itself a finding — write "not recorded" rather than
deleting the line, because the gap is what a reader needs to know about.

---

## 1. What was run

| | |
|---|---|
| Date (UTC) | |
| Operator | |
| Chapter / script | |
| Question being asked | |

## 2. Inputs

| | |
|---|---|
| PDB entries | |
| Downloaded from | `https://files.rcsb.org/download/<ID>.pdb` |
| Date fetched | |
| SHA-256 of each file | |
| Ligand SMILES (as docked, with formal charges) | |
| Protonation state assumed, and at what pH | |

A charge is part of the input. The series here spans −1 and −2; docking the
drawn neutral forms gets every member wrong by a different amount.

## 3. Preparation decisions

Each of these changes the answer. Record the choice, not just the result.

| Decision | Choice | Why |
|---|---|---|
| Chain used | | |
| Ligand copy used, and how selected | | by distance to Ser64 OG, not file order |
| Altlocs — which retained | | |
| Waters — deleted or kept | | 1L2S HOH 403 and 481 bridge the ligand; deleting them makes the crystal pose unreachable |
| Ions / crystallisation additives removed | | phosphates here are 7.83 Å or further from Ser64 OG |
| Missing residues — modelled or left | | |
| Structures excluded, and on what grounds | | 1GA9 is covalent to Ser64 (LINK, 1.64 Å); non-covalent docking cannot represent it |

## 4. Docking parameters

| | |
|---|---|
| Program and exact version | |
| **Seed** | |
| Exhaustiveness | |
| Number of modes | |
| Box centre (x, y, z) | |
| Box size (x, y, z) | |
| How the box was derived | e.g. ligand centroid + 8 Å padding |
| Flexible residues, if any | |

**The seed is not optional.** Vina's default seed is 0, which means *random*.
Two runs at the default differ and nothing in the log says so.

**A box too small for the ligand raises no error** — it returns a worse score
that looks like a result. Record the size so the score can be interpreted.

## 5. Scoring and comparison

| | |
|---|---|
| RMSD tool and version | |
| Symmetry-corrected? | must be yes |
| Superposition applied? | **must be no** |
| Reference pose (file and provenance) | |

`--minimize` superimposes before measuring and makes every validation pass. A
pose displaced 3.0 Å returns `3.00000` without it and `0.00000` with it. If the
record says superposition was applied, the RMSD in it means nothing.

## 6. Environment

| | |
|---|---|
| OS and version | |
| CPU, core count used | |
| `conda list --explicit` attached? | |
| Any package not from `environment.yml` | |

## 7. Results

| Quantity | Value | Expected (book) | Match? |
|---|---|---|---|
| | | | |

## 8. Deviations and anomalies

Anything that did not go as the protocol says, including things that turned out
not to matter. This section is the reason the record is worth keeping.
