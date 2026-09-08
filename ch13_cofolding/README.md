# Chapter 13 — co-folding

## Run

```bash
bash ch13_cofolding/run.sh
```

Writes the Boltz-2 input and attempts the prediction. On a machine without a
GPU the attempt exits 3 with an explanation. **Nothing is simulated.**

## The input is half the protocol

`outputs/ampc_stc.yaml` is written whether or not the model runs, because a
reader can check it without a GPU. Three things in it are easy to get wrong and
impossible to notice afterwards.

**The signal peptide.** UniProt P00811 residues 1–19 are a signal peptide that
is not in the crystal structure. Folding it with the complex hands the model 19
residues of something that is not there.

**The numbering, twice over.** The file is in UniProt numbering; the crystal is
not. And the *mature sequence* introduces a second offset, which composes with
the first:

```
mature position = UniProt − 19 = (PDB + 16) − 19 = PDB − 3
```

The script's own frame check caught this being written as plain `PDB` while the
chapter was being built. It now verifies **four** residues rather than one —
Ser64, Lys67, Tyr150 and Thr316 — because a check on Ser64 alone passes against
any of the twenty serines in the sequence:

```
PDB 64   -> UniProt 80   -> mature 61    S  expected S  ok
PDB 67   -> UniProt 83   -> mature 64    K  expected K  ok
PDB 150  -> UniProt 166  -> mature 147   Y  expected Y  ok
PDB 316  -> UniProt 332  -> mature 313   T  expected T  ok
```

On any mismatch the script stops. A sequence one residue out of frame folds
into something plausible and entirely wrong.

**The charge.** The SMILES carries an explicit −1. Co-folding models take
SMILES, and their handling of formal charge is not always documented — which is
worth checking before trusting a pose.

## Why it did not run here

Boltz-2 needs a CUDA GPU and several gigabytes of weights. This is a CPU-only
Windows machine.

**`pip install boltz` was attempted during this build. It succeeds — and it
downgrades numpy to 1.26, gemmi to 0.6.5 and scipy to 1.13**, silently breaking
the pinned environment that every other chapter depends on. The environment had
to be reinstalled and the full test suite re-run to confirm the repair.

**Install co-folding models in a separate environment.** That is a specific,
reproducible finding from this build rather than general hygiene advice, and it
is recorded in `build-record/PROGRESS.md`.

## What would have to be checked

1. **Renumber.** The model works in UniProt numbering; the crystal does not.
2. **Superimpose on the receptor**, then measure the ligand RMSD with no
   further fitting — heavy-atom and symmetry-corrected, as in Chapter 17. A
   co-folded complex arrives in its own frame, and superimposing on the
   **ligand** is the `--minimize` mistake wearing a different hat.
3. **Compare the predicted affinity against 26 µM** while remembering Chapter
   14: r = 0.62 on a benchmark is r² = 0.38, and this series spans
   0.32 kcal/mol — below what any current method resolves.
