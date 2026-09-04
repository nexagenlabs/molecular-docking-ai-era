# Chapter 24 — network pharmacology

Hit list 120 genes, pathway 80 genes, overlap 10. One experiment, three
defensible backgrounds.

| Background | Size | Expected overlap | Fold enrichment | p-value | Significant? |
|---|---|---|---|---|---|
| **assayed** | 1500 | 6.40 | 1.56 | 0.0993 | **no** |
| **expressed** | 12000 | 0.80 | 12.50 | 6.25e-09 | yes |
| **genome** | 20000 | 0.48 | 20.83 | 4.78e-11 | yes |

What each background means:

- **assayed** (1500) — genes the assay could actually detect. a targeted panel; the screen could only ever have hit these
- **expressed** (12000) — genes expressed in the tissue the screen was run in. a gene not expressed here could never have been a hit
- **genome** (20000) — every annotated protein-coding gene. the default in most tools, and the one nobody chose on purpose

The same twelve genes are 0.0993 against 4.78e-11 depending only on what
you counted as *could have been a hit*. Nothing in a tool's output
tells you which universe it used.

## The refusal

```
$ python ch24_network_pharmacology/scripts/enrichment.py
REFUSING TO RUN: no background gene list given.
```

Exit code 2, no result. Not a warning, not a default with a note in the
log. A p-value computed against an unstated background is not a weaker
result — it is not a result — and it will still print to three decimals
and go into a figure.

This is the only script in the repository that refuses to do the thing
it is for. That is the chapter.
