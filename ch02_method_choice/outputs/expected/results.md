# Chapter 2 — choosing a method

Every row below is read out of another chapter's output file. Nothing
is asserted from the literature or from memory, and a criterion whose
chapter has not been run says so rather than guessing.

| Question | What was measured | What follows | From |
|---|---|---|---|
| Rigid receptor, or flexible side chains? | 3 of the site residues change rotamer across 8 chains (Gln120, Leu293, Thr316); 8 stay inside 20 degrees in every torsion. | Rigid receptor is defensible. If you make anything flexible, make it exactly those 3 and nothing else. | ch10 |
| Crystal structure, or a predicted one? | The AlphaFold model has pLDDT 98.5 at the site and a backbone 0.216 A from the crystal, and docking into it gives 3.140 A against 1.114 A for the crystal structure. | Use the crystal structure when one exists. A near-perfect backbone did not buy a near-crystal pose, and no confidence metric predicted that. | ch06 |
| Does the protocol reproduce a known pose? | Redock RMSD: 1L2S 1.11 A, 4JXS 3.00 A, 4JXV 10.53 A. | 1 of 3 under 2 A. Validate before trusting any prospective result, and report the failures -- a protocol validated on its best case has not been validated. | ch17 |
| Can any method rank this series? | The series spans 0.32 kcal/mol, so ranking its ends at 95% confidence needs sigma below 0.116. The best statistical error any of these methods reports is 0.20. | No. Choose a different question, or a different series. This is the cheapest finding in the book and the one most often skipped. | ch22 |
| What would a good ML predictor buy here? | At r = 0.62 -- Boltz-2's reported figure, r-squared = 0.38 -- two compounds 0.32 kcal/mol apart are ordered correctly 54.8% of the time. | 4.8 points better than a coin flip. The limit is the question, not the method. | ch14 |
| What would a screen cost? | 4.97 s per compound measured on 4 cores; 5,518 core-hours for a million compounds. | Affordable. Cost is not the constraint here -- what you do with the ranking is. | ch12 |
| Is the ranking any good? | Published LIT-PCBA medians: Vina EF1% 0.90, GNINA 1.88 to 2.58. EF = 1.0 is chance. | Vina's ranking is below chance on that benchmark. Rescore, and expect a factor of two rather than a solved problem. | ch16 |

## Why this chapter is second and was built last

Method choice is normally made from reputation, before any measurement
exists — which is the only order in which it *can* be made, the first
time. This chapter makes the same decision in the other order, from the
measurements the rest of the book produced, so a reader can see what the
reputation-based answer would have got right and wrong.

The most useful row is the one about whether the question can be
answered at all. It costs two lines of arithmetic, it comes back *no*
for this series, and it is the step most often skipped — because it is
the only one that can tell you not to run the calculation.
