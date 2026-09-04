# Chapter 3 — databases

Every fact in this repository comes from somewhere. This chapter asks the
follow-up: **does the source agree with itself?**

## Run

```bash
bash ch03_databases/run.sh
```

Needs network access for the RCSB REST API.

## Structures, by two independent routes

Resolution and R-free from the REST API, against the header of the coordinate
file this repository downloaded:

| Entry | Resolution (API / file) | R-free (API / file) | Agree? |
|---|---|---|---|
| 1L2S | 1.94 / 1.94 | 0.207 / 0.207 | yes |
| 4JXS | 1.90 / 1.90 | 0.212 / 0.212 | yes |
| 4JXV | 1.76 / 1.76 | 0.232 / 0.232 | yes |
| 1GA9 | 2.10 / 2.10 | 0.249 / 0.249 | yes |

All four agree, which is the boring and correct outcome. It is still worth
running, because the alternative — quoting one route and assuming the other
matches — is how a stale number survives for years.

## The trap that is in both routes

The API's `refine` record holds `ls_R_factor_R_free` (0.207) directly beside
`ls_number_reflns_R_free` (**2647**). The coordinate file sets exactly the same
trap: `FREE R VALUE` sits a few lines from `FREE R VALUE TEST SET COUNT`.

A loose match on either one reports 2647 as an R-free. That is not hypothetical
— it happened in this repository's own Chapter 5 script and was caught by the
expected values. **The API is not safer than the file. It fails the same way.**

## Ligands, against the chemical component dictionary

| Ligand | Formula | Same neutral skeleton? |
|---|---|---|
| STC | C11 H8 Cl N O4 S2 | yes |
| 18U | C13 H11 N O6 S2 | yes |
| 1MU | C14 H13 N O6 S2 | yes |

The comparison is against the **neutral** skeleton on purpose. The PDB
component describes the molecule as modelled in the crystal, which carries no
protonation state for pH 7.4; this repository docks STC at −1 and 18U and 1MU
at −2. Those are different molecules and the difference is the subject of
Chapter 8. So what is checked here is that the skeleton matches and the charge
is *expected* to differ — a check that passed for the wrong reason would be
worse than no check.

## Affinity, and a disagreement kept open

| Ligand | ChEMBL | PDBbind | |
|---|---|---|---|
| STC | 26 µM | 26 µM | agree |
| 18U | 18 µM | 18 µM | agree |
| 1MU | 26 µM | 31 µM | **disagree** |

Both 1MU values are carried to the end rather than one being picked. Chapter 26
shows why: the disagreement between the sources is larger than the gap between
1MU and STC that a method would have to resolve in order to rank them.

**ETP is 83 nM**, measured with a different substrate and buffer. Not
comparable to the values above, and never converted. No conversion between Ki,
IC50 and Kd happens anywhere in this repository.
