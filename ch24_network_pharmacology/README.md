# Chapter 24 — network pharmacology

The only script in this repository that refuses to do the thing it is for.

## Run

```bash
bash ch24_network_pharmacology/run.sh
```

The first thing it does is fail:

```
$ python ch24_network_pharmacology/scripts/enrichment.py
REFUSING TO RUN: no background gene list given.
```

Exit code 2, no result. Not a warning, not a default with a note in the log.

## Why

A pathway-enrichment p-value is a statement about a hit list **relative to a
universe of genes that could have been hits**. Change the universe and the
p-value changes. Most tools pick one silently — usually the whole annotated
genome — and that is almost always wrong for a screen, because a screen could
only ever have hit what it assayed.

A p-value computed against an unstated background is not a weaker result. It is
not a result. And it will still print to three decimals and go into a figure,
which is why the refusal has to be a non-zero exit rather than a caveat.

## What the choice is worth

120 hits, an 80-gene pathway, 10 of the hits in it:

| Background | Size | Expected overlap | Fold enrichment | p-value | Significant? |
|---|---|---|---|---|---|
| assayed | 1,500 | 6.40 | 1.56 | 0.0993 | **no** |
| expressed | 12,000 | 0.80 | 12.50 | 6.25 × 10⁻⁹ | yes |
| genome | 20,000 | 0.48 | 20.83 | 4.78 × 10⁻¹¹ | yes |

Same hits. Same pathway. Same overlap. The p-value moves by a factor of **two
billion**, the fold enrichment by 13×, and the three backgrounds **do not agree
on whether the result is significant at all**.

Each background is defensible:

- **genome** — every annotated protein-coding gene. The default in most tools,
  and the one nobody chose on purpose.
- **expressed** — genes expressed in the tissue. A gene not expressed here
  could never have been a hit.
- **assayed** — genes the assay could detect. A targeted panel could only ever
  have hit these.

The narrowest background is usually the honest one, and it is the one that
kills the result.

## Arithmetic

The hypergeometric survival function is summed in exact integer arithmetic and
divided as a `Fraction`. `comb(20000, 120)` has 318 digits, so dividing it in
floating point raises `OverflowError` — which is the *good* outcome. The bad
one is a library that quietly returns `0.0` and lets a p-value of zero into a
figure.

Cross-checked against `scipy.stats.hypergeom`; the two agree to 8 × 10⁻¹⁷.

## A note on the worked example

The overlap of 10 was chosen so the three backgrounds disagree about
significance, because p < 0.05 is the decision rule people actually apply. At
11 or more, all three call it significant and the demonstration is only about
effect size. That is a teaching decision and it is stated in the script rather
than left looking like data.
