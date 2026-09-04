# Chapter 10 — flexible residues

Which binding-site side chains actually move, measured across four structures
and eight chains.

## Run

```bash
bash ch10_flexibility/run.sh
```

## The result

| | Residues |
|---|---|
| **Change rotamer** | **Gln120, Leu293, Thr316** |
| Move > 20° within one rotamer well | Tyr150 |
| Rigid — ≤ 20° in every rotamer-defining torsion | Ser64, Lys67, Leu119, Asn152, Tyr221, Lys315, Asn346, Arg349 |
| No side-chain torsion | Gly317, Ala318 |

Fourteen site residues; three of them move. Flexible-side-chain docking costs
search time that grows with the number of flexible residues, so the useful
question is not which residues *could* move but which are *observed* to. Eight
structures of the same protein answer it, and **Gln120, Leu293 and Thr316 are
the only defensible choices**.

## Two questions, not one

`CLAUDE.md` asks both, and they are different:

- *Does it vary by more than 20°?* — is the side chain still at all?
- *Does it change rotamer?* — did it move to a different well?

Tyr150 is the reason to keep them apart: it varies by 34.6° and never leaves
its rotamer well. That is a side chain breathing, not switching. Conflating the
two questions puts it on the flexible list and costs search time for nothing.

## Three ways to get this wrong

Each of these was a real error in this script before the expected values caught
it:

- **Ignoring the wrap-around.** −179° and +179° are two degrees apart, not 358.
  A naive max-minus-min reports half the site as rotameric.
- **Ignoring terminal symmetry.** The last χ of Tyr and Phe is defined only
  modulo 180°, because swapping CD1/CD2 gives the same physical ring.
- **Trusting terminal groups.** Asn χ2 and Gln χ3 record which way round an
  amide was *modelled* — O and N are not distinguishable at these resolutions,
  so a difference between chains is a refinement choice, not an observation.
  Lys χ4 and Arg χ4 are solvent-exposed and barely restrained. Include them and
  **Lys67 looks rotameric on the strength of χ4 alone**, while its χ1–χ3 vary
  by at most 19°.

The third one matters most: with all torsions counted naively, this analysis
returns eight rotamer-changing residues instead of three, and every one of the
five extra is a terminal-group artefact.

## Values this chapter must reproduce

Torsion analysis across the four structures and eight chains must return
**Gln120, Leu293 and Thr316** as the rotamer-changing residues, with **eight**
of the site residues varying ≤ 20° in every torsion.
