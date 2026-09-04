# 1L2S -- receptor QC

Resolution 1.94 A, R-free 0.207.

Catalytic Ser64 OG present in chains: A, B

> Numbering trap: UniProt number = PDB number + 16. Ser64 here
> is Ser80 in UniProt P00811 and in the AlphaFold model.

## Chain breaks (REMARK 465)

- chain A: LYS 290, ILE 291, ALA 292

A gap near the site is a reason to use the other chain, not
something to model over quietly.

## Disordered side chains (REMARK 470)

- chain A: 10 residues
  - GLU 21 missing CG CD OE1 OE2
  - GLN 22 missing CG CD OE1 NE2
  - LYS 99 missing CG CD CE NZ
  - GLU 124 missing CG CD OE1 OE2
  - LYS 126 missing CG CD CE NZ
  - GLU 196 missing CG CD OE1 OE2
  - LYS 207 missing CG CD CE NZ
  - LYS 246 missing CG CD CE NZ
  - ASP 264 missing CG OD1 OD2
  - ARG 296 missing CG CD NE CZ NH1 NH2
- chain B: 10 residues
  - GLN 7 missing CG CD OE1 NE2
  - GLN 52 missing CG CD OE1 NE2
  - GLN 57 missing CG CD OE1 NE2
  - ASP 123 missing CG OD1 OD2
  - LYS 126 missing CG CD CE NZ
  - GLU 205 missing CG CD OE1 OE2
  - LYS 207 missing CG CD CE NZ
  - LYS 246 missing CG CD CE NZ
  - LYS 290 missing CG CD CE NZ
  - LYS 299 missing CG CD CE NZ

Two defensible treatments, and they are not equivalent:

- **Type the residue down to what is present.** A lysine
  missing CG, CD, CE and NZ holds exactly alanine's heavy
  atoms, so alanine is an honest description of the file.
  Cheap, and it changes the chemistry of that position.
- **Rebuild the missing atoms** with PDBFixer or a similar
  tool. Keeps the residue identity, at the cost of atoms
  that are modelled rather than observed.

Deleting the whole residue is the option to avoid near the
site: it removes backbone as well, and leaves a hole that
nothing in the output mentions.

## Alternate locations

- GLN B250: altlocs A, B

Pick one and record which. The choice is arbitrary; leaving
it unrecorded is what makes it irreproducible.

## Ligand copies

| Group | Atoms | Distance to Ser64 OG | Verdict |
|---|---|---|---|
| STC A/1115 | 19 | 2.70 A | catalytic |
| STC B/2115 | 19 | 2.70 A | catalytic |
| STC B/3115 | 19 | 22.72 A | **NOT in an active site** |

Select by this distance, never by file order. Nothing in the
file marks which copy is the one you meant.

## Solvent, ions and additives

352 waters.

## Phosphate

None. (1L2S was not crystallised from phosphate; a phosphate
reported here would mean the HETATM parsing is wrong.)

## Bridging waters

Within 3.5 A of both a ligand copy and a protein side chain:

- **STC A/1115**
  - HOH A/401, 2.94 A from the ligand, contacts Arg349, Asn346
- **STC B/2115**
  - HOH B/403, 2.68 A from the ligand, contacts Arg349, Asn346
  - HOH B/481, 2.70 A from the ligand, contacts Lys315, Thr316, Tyr150

**Deleting these makes the crystallographic pose unreachable**
by docking. Keeping them fixes a water where a ligand atom
might belong. Neither is the safe default; the decision has to
be made and recorded.
