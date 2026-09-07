# Chapter 2 — choosing a method

Every recommendation here is read out of another chapter's output file.

## Run

```bash
bash ch02_method_choice/run.sh
```

A criterion whose chapter has not been run reports **"not measured"** rather
than falling back to a default — a default here is a guess wearing a number.

## Depends on seven other chapters

This chapter computes nothing. Every row is read out of a file another chapter
produced, and one row per file:

| Reads | Produced by | Feeds the row |
|---|---|---|
| `ch06_predicted_structures/outputs/alphafold_comparison.json` | `bash ch06_predicted_structures/run.sh` | Crystal structure, or a predicted one? |
| `ch10_flexibility/outputs/rotamers.json` | `bash ch10_flexibility/run.sh` | Rigid receptor, or flexible side chains? |
| `ch12_screening/outputs/screen.json` | `bash ch12_screening/run.sh` | What would a screen cost? |
| `ch14_boltz2/outputs/correlation.json` | `bash ch14_boltz2/run.sh` | What would a good ML predictor buy? |
| `ch16_rescoring/outputs/rescoring.json` | `bash ch16_rescoring/run.sh` | Is the ranking any good? |
| `ch17_validation/outputs/validation.json` | `bash ch17_validation/run.sh` | Does the protocol reproduce a known pose? |
| `ch22_free_energy/outputs/power.json` | `bash ch22_free_energy/run.sh` | Can any method rank this series? |

Run this chapter with none of them and it prints seven **NOT MEASURED** rows
and the sentence *"These are gaps, not defaults. Run the chapter."* Run it with
some of them and it prints the ones it has. It never fills a gap.

There is deliberately **no ch26 entry**, although the ranking question is also
Chapter 26's subject. This chapter answers it from Chapter 22's arithmetic --
the series spread against the precision the methods report -- and listing ch26
as a source claimed a dependency the code did not have.

## What it concludes for this system

| Question | What was measured | What follows |
|---|---|---|
| Rigid receptor, or flexible side chains? | 3 of 14 site residues change rotamer across 8 chains; 8 stay inside 20° in every torsion | Rigid is defensible. If anything is flexible, make it exactly Gln120, Leu293 and Thr316 |
| Crystal structure, or a predicted one? | AlphaFold pLDDT 98.5 at the site, backbone 0.216 Å — and docking into it gives 3.140 Å against the crystal's 1.114 Å | Use the crystal when one exists. **No confidence metric predicted that gap** |
| Does the protocol reproduce a known pose? | 1L2S 1.11 Å, 4JXS 3.00 Å, 4JXV 10.53 Å | 1 of 3 under 2 Å. Report the failures — a protocol validated on its best case has not been validated |
| **Can any method rank this series?** | Spread 0.32 kcal/mol; ranking its ends needs σ < 0.116; best available is 0.20 | **No.** Change the question or the series |
| What would a good ML predictor buy? | At r = 0.62 (r² = 0.38), two compounds 0.32 kcal/mol apart are ordered correctly 54.8% of the time | 4.8 points better than a coin flip. The limit is the question, not the method |
| What would a screen cost? | 4.97 s per compound on 4 cores; ~5,500 core-hours per million | Affordable. Cost is not the constraint — what you do with the ranking is |
| Is the ranking any good? | LIT-PCBA: Vina EF1% 0.90, GNINA 1.88–2.58, **chance = 1.0** | Vina is below chance there. Rescore, and expect a factor of two |

## Why this chapter is second and was built last

Method choice is normally made from reputation, before any measurement exists —
which is the only order in which it *can* be made, the first time. This chapter
makes the same decision in the other order, so a reader can see what the
reputation-based answer would have got right and wrong.

For this system, reputation would have got two things wrong. It would have
reached for the AlphaFold model, because the pLDDT is 98.5 and the backbone is
0.216 Å — and lost 2 Å of pose accuracy. And it would have tried to rank the
series, because ranking a congeneric series is what these methods are for.

## The row that matters most

**"Can any method rank this series?"** costs two lines of arithmetic, comes
back *no*, and is the step most often skipped — because it is the only one that
can tell you not to run the calculation.

Chapters 14, 22 and 26 reach that answer independently: from the correlation a
method reports, from the precision the question needs, and from trying the
ranking and failing. Three routes, one answer, and the cheapest of the three
could have been run first.
