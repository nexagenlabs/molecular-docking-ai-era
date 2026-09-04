# Chapter 13 — co-folding

## The input

`ampc_stc.yaml` — written whether or not the model can run, because the input is
half the protocol and can be checked without a GPU.

| | |
|---|---|
| UniProt | P00811 |
| Sequence | mature protein, 358 residues (signal peptide 1–19 removed) |
| Ligand | STC, SMILES with explicit −1 |
| Seed | 42 |
| Diffusion samples | 5 |

Three things in that file are easy to get wrong and impossible to
notice afterwards:

- **The signal peptide.** UniProt P00811 residues 1–19 are a signal
  peptide that is not in the crystal structure. Folding it with the
  complex hands the model 19 residues of something that is not there.
  The script verifies the boundary by checking that residue 64 of the
  mature sequence is a serine, and stops if it is not.
- **The numbering.** The file is in UniProt numbering: Ser80 here,
  Ser64 in every PDB file in this repository. Chapter 6 shows the
  failure mode — asking a model for residue 64 returns isoleucine, with
  no error raised.
- **The charge.** The SMILES carries an explicit −1. Co-folding models
  take SMILES and their handling of formal charge is not always
  documented, which is worth checking before trusting a pose.

## The prediction did not run here

Boltz-2 needs a CUDA GPU and several gigabytes of weights. This is a
CPU-only Windows machine.

**`pip install boltz` was attempted during this build.** It succeeds
— and it downgrades numpy to 1.26, gemmi to 0.6.5 and scipy to 1.13,
silently breaking the pinned environment every other chapter depends
on. The environment had to be reinstalled. **Install co-folding
models in a separate environment**, which is a specific and
reproducible finding rather than general advice.

The command this chapter would run, and what would then have to be
checked, are printed by the script. Nothing is simulated.

## What would have to be checked

1. Renumber. The model works in UniProt numbering, the crystal does not.
2. Superimpose on the RECEPTOR, then measure the ligand RMSD with no
   further fitting -- heavy-atom and symmetry-corrected, as in ch17. A
   co-folded complex arrives in its own frame, and superimposing on the
   LIGAND is the --minimize mistake wearing a different hat.
3. Compare the predicted affinity against 26 uM while remembering ch14:
   r = 0.62 on a benchmark is r-squared = 0.38, and this series spans
   0.32 kcal/mol -- below what any current method resolves.
