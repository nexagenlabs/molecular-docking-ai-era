# Chapter 10 — which side chains actually move

Every side-chain torsion of the 14 binding-site residues, across the 8 chains of
1L2S, 4JXS, 4JXV and 1GA9.

| Residue | Largest spread | Verdict |
|---|---|---|
| Gln120 | 169.7° | **changes rotamer** |
| Leu293 | 150.8° | **changes rotamer** |
| Thr316 | 142.7° | **changes rotamer** |
| Tyr150 | 34.6° | moves, same well |
| Lys67 | 19.3° | rigid |
| Asn152 | 17.2° | rigid |
| Leu119 | 15.7° | rigid |
| Asn346 | 14.6° | rigid |
| Arg349 | 13.9° | rigid |
| Lys315 | 12.1° | rigid |
| Tyr221 | 10.6° | rigid |
| Ser64 | 10.2° | rigid |
| Ala318 | — | no side-chain torsion |
| Gly317 | — | no side-chain torsion |

**Gln120, Leu293, Thr316** are the rotamer-changing residues, and the only
defensible choices for flexible-residue docking here.

8 residues stay inside 20° in every rotamer-defining torsion across
all 8 chains. 2 have no side-chain torsion at all.

Tyr150 moves more than 20° and still stays in one rotamer well. That
is a side chain breathing rather than switching, and it is why
"varies by more than 20°" and "changes rotamer" have to be asked
as two separate questions.

## Three ways to get this wrong

- **Ignoring the wrap-around.** −179° and +179° are two degrees apart,
  not 358. A naive max-minus-min reports half the site as rotameric.
- **Ignoring terminal symmetry.** The last χ of Tyr and Phe is defined
  only modulo 180°, because swapping CD1/CD2 gives the same ring.
- **Trusting terminal groups.** Asn χ2 and Gln χ3 record which way an
  amide was modelled, not which way it points — O and N are
  indistinguishable at this resolution. Lys χ4 and Arg χ4 are
  solvent-exposed and barely restrained. Include them and Lys67 looks
  rotameric on χ4 alone, while its χ1–χ3 vary by at most 19°.
