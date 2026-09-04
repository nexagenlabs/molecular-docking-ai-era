# Chapter 8 — ligand preparation

Protonation, stereochemistry and conformer generation, in the order they bite.

## Run

```bash
bash ch08_ligand_prep/run.sh
```

Writes `outputs/ligand_prep.md` and `outputs/ligand_prep.json`.

## Charge is part of the molecule's identity

| Ligand | Drawn | At pH 7.4 | Ki |
|---|---|---|---|
| STC | 0 | **−1** | 26 µM |
| 18U | 0 | **−2** | 18 µM |
| 1MU | 0 | **−2** | 26 µM (ChEMBL) / 31 µM (PDBbind) |

The series spans −1 and −2. Docking the drawn neutral forms is therefore wrong
by a *different amount for each member*, which corrupts the ranking rather than
shifting it — and a corrupted ranking still looks like a result. If it shifted
everything equally you would at least still have the right order.

The script treats the charges as a **hard failure**, not a printed line: if a
future RDKit changes protonation behaviour, the build breaks loudly rather than
quietly docking the wrong species.

The 1MU Ki disagrees between sources. Both are reported; neither is chosen.

## Conformers are generated from the deprotonated form

This is the part worth reading twice. **Protonation comes first.** The conformer
search runs on the charged species — the molecule that will actually be docked —
not on the neutral form as drawn.

That ordering is not cosmetic. The two forms are genuinely different molecules
and give different counts, so a search run on the drawn molecule explores the
shape of something nobody docks. The chapter prints **both columns** anyway: a
conformer count published without saying which form produced it cannot be
reproduced, and that is not a hypothetical — reproducing the book's table
required establishing which form it used, and the first answer was wrong.

## Values this chapter must reproduce

RDKit ETKDGv3, 300 attempts, `pruneRmsThresh=0.5`, seeds 1 / 7 / 42 / 99 / 2026,
deprotonated form:

| Ligand | Rotatable bonds | Conformers by seed |
|---|---|---|
| STC | 4 | 15, 15, 16, 16, 16 |
| 18U | 6 | 9, 9, 12, 11, 8 |
| 1MU | 7 | 33, 35, 33, 28, 37 |

**Conformer counts do not track rotatable-bond count.** 18U has two more
rotatable bonds than STC and yields fewer conformers. That is the teaching
point of the chapter and must not be "fixed" — the 0.5 Å prune works on
geometry, not topology, so a molecule whose extra torsions lead to similar
shapes collapses under it.

Counts also move with the seed: 1MU spans 28 to 37 across five seeds, a range of
a third of its own value. One seed tells you nothing about how stable a count is.

**Platform.** These counts are exact on Linux. On Windows the same RDKit
2026.3.5 reproduces the STC row exactly and differs by one to three elsewhere
(18U 9, 9, **11**, 11, 8; 1MU 33, 35, 33, **29**, **34**) — the same build-level
difference documented in Chapter 9, where it moves docking scores rather than
conformer counts. The tests assert the exact counts on Linux and mark them xfail
elsewhere, with the reason attached.

## Stereochemistry

All three ligands are achiral, so the SDF round-trip preserves the canonical
isomeric SMILES trivially. The check is kept anyway: it costs nothing to run,
and it is what will catch the day a chiral analogue joins the series.
