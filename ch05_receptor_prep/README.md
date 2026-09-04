# Chapter 5 — receptor preparation

A quality-control report for a crystal structure, run **before** anyone docks
into it.

## Run

```bash
bash ch05_receptor_prep/run.sh
```

Or for any entry you like:

```bash
python ch05_receptor_prep/scripts/qc_report.py 1L2S 4JXS
```

Writes `outputs/qc_<PDBID>.md` and `outputs/qc_<PDBID>.json`.

## What it reports, and why each line is there

| Reported | The failure it prevents |
|---|---|
| Resolution and R-free | Quoting a structure's quality from memory |
| Chain breaks (REMARK 465) | Docking into a chain with a hole near the site |
| Disordered side chains (REMARK 470) | A residue silently missing half its atoms |
| Alternate locations | Two people taking different altlocs and comparing results |
| Every HETATM group, with its distance to Ser64 OG | Docking the wrong copy of the ligand |
| Bridging waters | Deleting the water the pose depends on |
| Phosphate | Mistaking a crystallisation additive for a bound ligand |
| Covalent links to Ser64 | Scoring a covalent complex with a non-covalent function |

**The distances are the point.** 1L2S contains three copies of STC. Two sit
2.70 Å from a catalytic Ser64 OG; the third is 22.72 Å from either, at a chain
interface. Nothing in the file marks which is which, and the one that comes
first is not the one you want. Select by distance, never by file order.

## The header has traps

`FREE R VALUE TEST SET COUNT` sits a few lines from `FREE R VALUE` and holds an
integer in the thousands. A prefix match on "FREE R VALUE" reports 2647 as an
R-free without complaint. Likewise `REMARK   2 RESOLUTION.` — take the token
after the label, not the first number on the line, or every structure comes
back at 2.00 Å. Both of those were live bugs in this script before the expected
values caught them.

## Disordered side chains: two honest options

Ten chain B side chains in 1L2S are listed in REMARK 470 as missing their
distal atoms. A lysine missing CG, CD, CE and NZ holds exactly alanine's heavy
atoms, which leaves two defensible treatments:

- **Type the residue down to what is present.** Cheap, needs no extra
  dependency, and honest about the file — but it changes the chemistry at that
  position, so a lysine's charge is gone. This is what
  `ch09_first_run/scripts/prepare_ampc.py` does, and it records which residues.
- **Rebuild the missing atoms with PDBFixer.** Keeps the residue identity at
  the cost of atoms that are modelled rather than observed:

  ```python
  from pdbfixer import PDBFixer
  from openmm.app import PDBFile

  fixer = PDBFixer(filename="1L2S.pdb")
  fixer.findMissingResidues()
  fixer.findMissingAtoms()
  fixer.addMissingAtoms()          # rebuilds REMARK 470 side chains
  fixer.addMissingHydrogens(7.4)
  PDBFile.writeFile(fixer.topology, fixer.positions, open("1L2S_fixed.pdb", "w"))
  ```

  PDBFixer is a conda-forge package and pulls in OpenMM, which is why this
  repository does not depend on it. **It is not installed here**, so the code
  above is documented rather than run — see `PROGRESS.md`.

Deleting the residue is the option to avoid anywhere near the site: it takes
the backbone with it and leaves a hole that nothing in the output mentions. In
1L2S, Lys290's centre of mass is only 1.1 Å outside the 20 Å box face.

## Values this chapter must reproduce

**1L2S** — 1.94 Å, R-free 0.207. Three STC copies at 2.70, 2.70 and 22.72 Å
from Ser64 OG. Chain A missing Lys290–Ala292. Sole altloc Gln250. Two bridging
waters in chain B: HOH 403 at 2.68 Å (contacts Asn346, Arg349) and HOH 481 at
2.70 Å (contacts Thr316, Lys315, Tyr150). **No phosphate** — one reported here
would mean the HETATM parsing is wrong, and so the ligand selection could not
be trusted either.

**4JXS, 4JXV, 1GA9** — nearest phosphate phosphorus to any Ser64 OG is
**7.83 Å**, in 4JXS. All surface artefacts from the 1.7 M potassium phosphate
crystallisation.

**1GA9** — covalent: `LINK` from Ser64 OG to ETP, 1.64 Å in chain A and 1.62 Å
in chain B. Also a K⁺ ion from crystallisation, named explicitly because AmpC
is a class C **serine** hydrolase with no catalytic metal, and a stray metal in
the input invites exactly the misreading this book warns against.
