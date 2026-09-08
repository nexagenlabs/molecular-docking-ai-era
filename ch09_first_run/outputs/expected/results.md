# Chapter 9 — expected results

Two systems. Only the first has published numbers.

| Part | System | Expected values? |
|---|---|---|
| 1 | synthetic — 10-heavy-atom ligand in a carbon shell | **yes**, and they are exact |
| 2 | AmpC — 1L2S chain B, STC | no published score |

The book's timing and box-size numbers were measured on the synthetic system,
deliberately: it costs seconds and anyone can repeat it. Docking STC into AmpC
gives entirely different scores and **must not be compared against them**.

---

## Part 1 — the synthetic system

Built by `scripts/make_test_system.py`: N-methylbenzamide embedded at RDKit
seed 11, MMFF-optimised, hydrogens kept; 140 carbons on a shell of radius
9.0–10.5 Å from `numpy.random.default_rng(3)`, centred on the origin. Box
centre (0, 0, 0), seed 42, exhaustiveness 8 for the sweep, 4 cores for timing.

### 1.1 The seed

| | Expected |
|---|---|
| seed 0, twice | **different** |
| seed 42, twice | **byte-identical** |

Vina's default seed is 0, which means random. Nothing in the log distinguishes
a defaulted seed from a fixed one.

### 1.2 Exhaustiveness

Book: 8 → 3.4 s, 32 → 14.2 s on 4 cores, ratio 4.18.

**Absolute times are hardware-specific. Assert only that the ratio is greater
than 1.5 and less than 4.0.** 4.0 is exact linearity — the grid is a fixed cost
paid once, so a faster machine amortises less of it over the short run and the
ratio falls. Measured: 4.18 on the book's machine, 3.34 on Windows, 2.80 on
Ubuntu 24.04; nothing has exceeded 4.0. This machine (Windows 11, 4 cores):
2.31 s and 8.20 s, ratio **3.55**. Record your own; do not tune to any of these.

### 1.3 Box size

Cube edges 20 / 12 / 8 Å, seed 42, exhaustiveness 8:

| Cube edge | Book | Native Linux | Native Windows |
|---|---|---|---|
| 20 Å | −4.905 | **−4.905** | −4.910 |
| 12 Å | −4.911 | **−4.911** | −4.903 |
| 8 Å | −2.748 | **−2.748** | −2.686 |

**On Linux the book's values reproduce to three decimals.** On Windows they do
not, and the reason is understood — see "Platform" below.

No error is raised at any size. The undersized box returns a number that looks
exactly like a result.

### 1.4 Mode 1's RMSD

Mode 1 reports `0.000 0.000`, always. The column is distance from mode 1, so
mode 1's distance from itself is zero by construction. It is not a comparison
with a crystal pose, and reading it as one is the most common way a docking run
appears to validate itself.

---

## Part 2 — AmpC

**No published expected score.** This is the system a reader actually works
with, and the chapter's job here is the protocol, not a number.

What the preparation must show, and does:

- Three STC copies found, at 2.70, 2.70 and **22.72 Å** from Ser64 OG. The copy
  is selected by that distance, never by file order.
- Every HETATM group not used is printed by name: 352 waters and the two
  unused STC copies.
- HOH 403 and 481 named specifically — they bridge the ligand to the protein at
  2.68 and 2.70 Å, and deleting them (which this chapter does) can put the
  crystallographic pose out of reach.
- Chain B, because chain A is missing Lys290–Ala292. Altloc A for Gln250.
- Ten disordered side chains typed as alanine, not deleted.
- Box centre 79.802, 5.352, 29.948, derived from the centroid of STC B/2115 and
  written into `config/vina_config.txt` by `scripts/derive_box.py`.

For the record, this machine gets −7.384 kcal/mol at seed 42 and exhaustiveness
8, with mode 1 at RMSD `0.000 0.000`. It is not a book value and nothing should
be tuned to reproduce it.

---

## Platform

**The three-decimal values in Part 1 are Linux values.** Measured on this
machine, same Vina 1.2.7, meeko 0.8.0 and RDKit 2026.3.5 throughout:

| Ligand built on | Docked with | 20 Å | 12 Å | 8 Å |
|---|---|---|---|---|
| Linux | Linux Vina | −4.905 | −4.911 | −2.748 |
| Windows | Linux Vina | −4.904 | −4.896 | −2.728 |
| Windows | Windows Vina | −4.910 | −4.903 | −2.686 |

Two independent causes, both established by experiment:

1. **The RDKit build.** Windows and Linux RDKit 2026.3.5 produce different
   MMFF-optimised coordinates from the same `EmbedMolecule(randomSeed=11)`. The
   receptor, built from numpy's PCG64, is byte-identical across the two — so it
   is the force field's convergence that differs, not the random stream.
2. **The Vina build.** Given identical input files, the Linux and Windows
   binaries return different scores.

The lesson generalises beyond this chapter: **seed 42 gives byte-identical
results within a build, not across builds.** Nothing in the log says which
situation you are in. Record the platform alongside the seed.
