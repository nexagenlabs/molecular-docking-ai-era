# Protocol record

The seventeen fields of the Chapter 20 record. Copy this file, fill it in, and
keep it with the results it describes. `ch17_validation` emits
`validation_record.md` in this shape.

**Tier one** is marked ★. Those seven fields are the ones whose absence stops
re-execution — without them nobody can run your protocol again, including you.
Everything else changes the answer; the tier-one fields decide whether there is
an answer at all.

A field you cannot fill is itself a finding. Write "not recorded" rather than
deleting the line: the gap is what a reader needs to know about.

---

## Header

| | |
|---|---|
| Date (UTC) | |
| Operator | |
| Chapter / script | |
| Question being asked | |

## Receptor

| Field | Value |
|---|---|
| ★ **Receptor source and identifier** | e.g. RCSB `files.rcsb.org`, 1L2S, fetched YYYY-MM-DD, SHA-256 … |
| **Chains and altlocs kept** | |
| **Waters and ions** | which deleted, which kept, and why |
| **Missing residues** | modelled or left as gaps |
| ★ **Receptor preparation tool and version** | |

A digest for the coordinate file matters as much as the accession: RCSB
re-releases entries, and a re-release changes your numbers for a reason that has
nothing to do with your protocol.

*Waters are not a formality here.* In 1L2S chain B, HOH 403 and HOH 481 bridge
the ligand to the protein at 2.68 Å and 2.70 Å. Delete them and the
crystallographic pose becomes unreachable by docking — the redock then fails
for a reason invisible in the output.

*Ions and additives.* The phosphates in 4JXS, 4JXV and 1GA9 are crystallisation
artefacts from 1.7 M potassium phosphate, the nearest 7.83 Å from any Ser64 OG.
1GA9 also carries a K⁺ ion. Record their removal explicitly — AmpC is a class C
**serine** hydrolase with no catalytic metal, and a reader who sees a metal in
your input and no note about it will assume you docked into the wrong enzyme.

*Ligand copy selection belongs here too.* 1L2S holds three copies of STC; two
are catalytic at 2.70 Å from Ser64 OG and one sits at a chain interface 22.7 Å
away. 4JXV holds 1MU in both chains — A/402 as a single conformer, B/401 in two
altlocs — so choosing a reference there is two decisions, chain and then
conformer. State how the copy was chosen, not just which one: by distance to
Ser64 OG is a protocol, by file order is an accident.

## Ligand

| Field | Value |
|---|---|
| ★ **Ligand source** | SMILES, and where it came from; or a PDB chemical component ID |
| **Ligand preparation** | conformer generation, seed, force field, protonation and at what pH |
| **Stereochemistry as docked** | |

The formal charge is part of the ligand identity, not an afterthought. This
series spans −1 (STC) and −2 (18U, 1MU), so docking the drawn neutral forms is
wrong by a *different* amount for each member — which corrupts the ranking
rather than shifting it, and a corrupted ranking still looks like a result.

PDBQT drops formal charge and reorders atoms. Keep an SDF as the reference copy
and convert outward only; a PDBQT round-trip silently returns the 18U dianion
as the neutral diacid in an atom order that breaks any RMSD measured against it.

## Search box

| Field | Value |
|---|---|
| ★ **Box centre** (x, y, z) | |
| ★ **Box dimensions** (x, y, z) | |
| **Box derivation** | e.g. centroid of the crystallographic ligand, 8 Å padding |

A box too small to hold the ligand **raises no error**. Edges of 20, 12 and 8 Å
on the same system return −4.905, −4.911 and −2.748; only the third looks
anomalous, and nothing in the output says why. The dimensions are what make the
score interpretable, and the derivation is what makes them reproducible.

## Docking

| Field | Value |
|---|---|
| ★ **Docking program and version** | exact version — Vina 1.2.5 was superseded in February 2025 |
| **Exhaustiveness / num_modes / energy_range** | |
| ★ **Random seed** | |

**The seed is tier one.** Vina's default seed is 0, which means *random*. Two
runs at the default differ; two at seed 42 are byte-identical. Nothing in the
log distinguishes a defaulted seed from a fixed one, so a record without this
field cannot be re-executed even though every other field is present.

## Results

| Field | Value |
|---|---|
| **Redocking result** | RMSD to the crystallographic pose, in Å |
| **Cross-docking or enrichment result** | |

State how the RMSD was computed, because two conventions give different numbers
from the same pair of files:

| | |
|---|---|
| RMSD tool and version | |
| Heavy-atom only? | must be yes |
| Symmetry-corrected? | must be yes |
| Superposition applied? | **must be no** |
| Reference pose (file and provenance) | |

`--minimize` superimposes before measuring, which discards exactly what a redock
tests. A pose displaced 3.0 Å returns `3.00000` without the flag and `0.00000`
with it — the flag makes every validation pass. If a record does not say
superposition was off, its RMSD means nothing.

## Environment

| | |
|---|---|
| OS and version | |
| CPU, core count used | |
| `environment/resolved.txt` attached? | |
| Anything not from `requirements.txt` | |

## Exclusions and deviations

What you left out and on what grounds, plus anything that did not go as the
protocol says — including things that turned out not to matter.

1GA9 is the worked example: ETP is covalently bound to Ser64 OG (`LINK`, 1.64 Å
in chain A, 1.62 Å in chain B), and non-covalent docking cannot represent that
bond. Excluding it is defensible; excluding it silently is not, because a reader
comparing your structure list against the PDB will find the gap and have no way
to tell a decision from an oversight.
