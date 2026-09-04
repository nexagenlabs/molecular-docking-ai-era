# Chapter 16 — rescoring

LIT-PCBA median EF1%, and what each is worth in compounds bought.

Library of 1,000,000, 0.1% genuinely active, 10 actives wanted in hand.

| Method | EF1% | Against chance | Compounds to test | Cost |
|---|---|---|---|---|
| random | 1.00 | **chance** | 10,000 | 500,000 |
| Vina | 0.90 | **worse** | 11,111 | 555,556 |
| GNINA (low) | 1.88 | better | 5,319 | 265,957 |
| GNINA (high) | 2.58 | better | 3,876 | 193,798 |

## EF = 1.0 is chance

**Vina's 0.90 is below it.** Ranking a library by Vina score and testing
the top slice finds fewer actives than testing the same number of
compounds picked at random — 11,111 tested against 10,000, for 55,556 more spent.

Quoted as *"GNINA 2.58 against Vina 0.90"*, this reads as one method
being about three times better than another method that works. One of
them does not work. Keep the 1.0 in the sentence.

## And GNINA's improvement is real, and modest

An EF1% of 2.58 means the top 1% of the ranked library is 2.58 times
richer in actives than the library as a whole. It does not mean that
2.58 out of every 3 hits are real, which is how the number tends to get
read. On the arithmetic above it takes you from 10,000 compounds to 3,876.

That is a genuine and useful gain. It is not a solved problem.
