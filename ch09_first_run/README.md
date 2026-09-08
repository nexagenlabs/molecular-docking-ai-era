# Chapter 9 — your first docking run

Four ways a docking run goes wrong while looking as though it went right, and
then the same protocol on a real protein.

## Run

```bash
bash ch09_first_run/run.sh
```

Requires the pinned environment — see
[`environment/README.md`](../environment/README.md). Vina is located through
`$VINA`, then `.tools/`, then `PATH`, and must report 1.2.7.

## Two systems, kept apart

**Part 1 is a synthetic system**: N-methylbenzamide, ten heavy atoms, inside a
shell of 140 carbon atoms. It is not a protein and is not meant to resemble
one. The book's timing and box-size numbers are these, deliberately — they cost
seconds and anyone can repeat them.

**Part 2 is AmpC**: 1L2S chain B and STC, the system a reader actually works
with. It has **no published expected score**, and its timings are nothing like
the synthetic ones.

Conflating the two is how a reader ends up expecting 14 seconds on a real
protein. `run.sh` runs them in order and labels them; the scripts take
`--system synthetic` or `--system ampc`.

## What each script shows

| Script | Shows |
|---|---|
| `scripts/make_test_system.py` | Builds the synthetic system from fixed seeds |
| `scripts/verify_run.py` | Seed 0 twice differs; seed 42 twice is byte-identical |
| `scripts/timing.py` | Exhaustiveness 8 against 32, and the ratio |
| `scripts/box_sweep.py` | 20 / 12 / 8 Å boxes, and that none of them errors |
| `scripts/modes.py` | Mode 1's RMSD columns, and why they are not validation |
| `scripts/prepare_ampc.py` | Builds the AmpC receptor and ligand, printing every decision |
| `scripts/derive_box.py` | Computes the box and writes it into `config/vina_config.txt` |

The box centre in `config/vina_config.txt` is written by `derive_box.py` rather
than typed, so it can be checked against the ligand it came from. Every line in
that config carries a comment saying where its value originated.

## The AmpC preparation, in detail

`prepare_ampc.py` prints each decision as it makes it:

- Picks the STC copy **by distance to Ser64 OG**, not by file order. 1L2S holds
  three; the script prints all three with their distances and discards B/3115
  at 22.72 Å.
- Prints **every HETATM group it did not use**, by name. A ligand quietly
  mis-picked is the failure this guards against, and it happens through a group
  nobody mentioned.
- Names HOH 403 and 481 specifically. They bridge the ligand to the protein at
  2.68 and 2.70 Å; this chapter deletes all waters, which is the usual default
  and is a decision, not a neutral act.
- Uses chain B, because chain A is missing Lys290–Ala292. Takes altloc A for
  Gln250, the entry's sole altloc.
- Types ten disordered chain B side chains as alanine. REMARK 470 lists them as
  missing their distal atoms, so what the file holds is exactly alanine's heavy
  atoms. Deleting the residues instead would remove backbone, and Lys290's
  centre of mass is only 1.1 Å outside the 20 Å box face. **Chapter 5 describes
  the alternative — rebuilding the missing atoms with PDBFixer — and when it is
  worth the extra dependency.**

## What to expect

Compare against
[`outputs/expected/results.md`](outputs/expected/results.md).

**On Linux the book's box-size values reproduce to three decimals**: −4.905 /
−4.911 / −2.748. On Windows they do not, and the reason is measured rather than
guessed — the Windows RDKit build optimises the ligand to slightly different
coordinates, and the Windows Vina build scores differently even when handed the
Linux ligand. `outputs/expected/results.md` has the full table.

The general lesson is worth more than the specific numbers: **seed 42 gives
byte-identical results within a build, not across builds**, and nothing in the
log tells you which situation you are in. Record the platform next to the seed.

## Values this chapter must reproduce

Vina 1.2.7, synthetic system, box centre (0, 0, 0), seed 42:

- Seed 0 twice → different. Seed 42 twice → byte-identical.
- Exhaustiveness 8 → 3.4 s, 32 → 14.2 s on 4 cores, ratio 4.18. **Absolute
  times are hardware-specific; only the band — greater than 1.5, less than 4.0
  — is asserted.** 4.0 is exact linearity, and a faster machine amortises less
  of the fixed grid cost, so the ratio falls: 4.18 on the book's machine, 3.34
  on Windows, 2.80 on Ubuntu 24.04. This machine: 2.31 s and 8.20 s, ratio 3.55.
- Box 20 / 12 / 8 Å → −4.905 / −4.911 / −2.748, **no error raised**.
- Mode 1 always reports RMSD `0.000 0.000` — distance from mode 1, not from a
  crystal pose.

This is the sample chapter and the pattern the others follow.
