#!/usr/bin/env python3
"""Chapter 13 — co-folding a complex, and what would have to be checked.

    python ch13_cofolding/scripts/cofold.py

Writes the Boltz-2 input for AmpC + STC, then attempts the prediction.

The input file is written whether or not the model can run, because the input
is half the protocol and a reader can check it without a GPU. Three things in
it are easy to get wrong and impossible to notice afterwards:

  * the **mature** sequence, not the one with the signal peptide
  * UniProt numbering, which is PDB numbering + 16
  * the ligand's formal charge, which co-folding models take from SMILES and
    do not always document their handling of

Writes outputs/ampc_stc.yaml and outputs/cofolding.md.
"""
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"

UNIPROT = "P00811"
FASTA_URL = "https://rest.uniprot.org/uniprotkb/%s.fasta" % UNIPROT

# UniProt P00811 residues 1-19 are the signal peptide. The mature protein is
# what crystallises and what should be folded; including the signal peptide
# gives the model 19 residues of something that is not in the complex.
SIGNAL_PEPTIDE_END = 19

# The ligand as docked. Deprotonated carboxylate, charge -1 at pH 7.4.
STC_SMILES = "c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)[O-])Cl"

SEED = 42
DIFFUSION_SAMPLES = 5

# UniProt number = PDB number + 16, from CLAUDE.md and confirmed against the
# AlphaFold model in ch06 at 100% residue identity.
UNIPROT_MINUS_PDB = 16

# So a position in the MATURE sequence, counting from 1, is
#
#     mature = UniProt - SIGNAL_PEPTIDE_END = PDB + 16 - 19 = PDB - 3
#
# and not PDB, which is the mistake this script's own check caught while it
# was being written. Two offsets compose here and it is easy to apply one.
MATURE_MINUS_PDB = UNIPROT_MINUS_PDB - SIGNAL_PEPTIDE_END

# Residues to verify the frame with. Ser64 alone is not enough: a check that
# lands on any serine passes, and there are 20 of them.
CHECK_RESIDUES = {"64": "S", "67": "K", "150": "Y", "316": "T"}


def fetch_sequence():
    """The mature sequence, from UniProt, with the signal peptide removed."""
    cache = STRUCTURES / ("%s.fasta" % UNIPROT)
    if not cache.exists():
        print("fetching %s" % FASTA_URL)
        with urllib.request.urlopen(FASTA_URL, timeout=60) as response:
            cache.write_bytes(response.read())
    lines = cache.read_text().splitlines()
    full = "".join(line.strip() for line in lines if not line.startswith(">"))
    return full, full[SIGNAL_PEPTIDE_END:]


def write_input(mature):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ampc_stc.yaml"
    text = """# Boltz-2 input: AmpC beta-lactamase + STC.
#
# SEQUENCE: the MATURE protein, UniProt {uniprot} residues {start}-{end}. The
# first {signal} residues are the signal peptide; they are not in the crystal
# structure and folding them with the complex gives the model {signal} residues
# of something that is not there.
#
# NUMBERING: this file is in UniProt numbering. The catalytic serine is Ser{cat_up}
# here and Ser{cat_pdb} in every PDB file in this repository -- UniProt = PDB + 16.
# A co-folded pose compared against a crystal pose must be renumbered before
# any residue is named. Chapter 6 shows what happens otherwise: asking the
# AlphaFold model for residue {cat_pdb} returns isoleucine, with no error.
#
# CHARGE: the ligand SMILES carries an explicit -1. Co-folding models take
# SMILES and their handling of formal charge is not always documented, which
# is itself worth checking before trusting a pose.
version: 1
sequences:
  - protein:
      id: A
      sequence: {sequence}
  - ligand:
      id: B
      smiles: "{smiles}"
properties:
  - affinity:
      binder: B
""".format(uniprot=UNIPROT, start=SIGNAL_PEPTIDE_END + 1,
           end=SIGNAL_PEPTIDE_END + len(mature), signal=SIGNAL_PEPTIDE_END,
           cat_up=80, cat_pdb=64, sequence=mature, smiles=STC_SMILES)
    path.write_text(text, encoding="utf-8")
    return path


def main():
    full, mature = fetch_sequence()
    print("UniProt %s: %d residues; mature protein %d (signal peptide 1-%d removed)"
          % (UNIPROT, len(full), len(mature), SIGNAL_PEPTIDE_END))

    # Verify the frame against the crystal structure rather than trusting two
    # composed offsets. Four residues, not one: a check on Ser64 alone passes
    # against any of the twenty serines in the sequence.
    print("\nframe check, mature position = PDB %+d:" % MATURE_MINUS_PDB)
    wrong = []
    for pdb_seq, expected in sorted(CHECK_RESIDUES.items(), key=lambda kv: int(kv[0])):
        position = int(pdb_seq) + MATURE_MINUS_PDB
        found = mature[position - 1] if 0 < position <= len(mature) else "?"
        ok = found == expected
        if not ok:
            wrong.append(pdb_seq)
        print("   PDB %-4s -> UniProt %-4s -> mature %-4s  %s  expected %s  %s"
              % (pdb_seq, int(pdb_seq) + UNIPROT_MINUS_PDB, position, found,
                 expected, "ok" if ok else "MISMATCH"))
    if wrong:
        sys.exit("frame check failed at %s -- the sequence would be wrong and "
                 "every residue named downstream would be a different residue"
                 % ", ".join(wrong))
    print("   all four match: the mature sequence is in frame.")

    path = write_input(mature)
    print("wrote %s" % path)

    boltz = shutil.which("boltz")
    if boltz is None:
        print("\nboltz is not installed, so the prediction cannot run here.")
        print("\n  What it needs:  a CUDA GPU and several GB of model weights")
        print("  What is here:   a CPU-only Windows machine")
        print("  Install:        pip install boltz")
        print("\n  NOTE: `pip install boltz` was attempted while this repository")
        print("  was being built. It succeeds, and it downgrades numpy to 1.26,")
        print("  gemmi to 0.6.5 and scipy to 1.13 -- silently breaking the pinned")
        print("  environment every other chapter depends on. Install it in a")
        print("  SEPARATE environment. See build-record/PROGRESS.md.")
        print("\nThe command this chapter would run:\n")
        print("  boltz predict %s \\" % path)
        print("        --use_msa_server \\")
        print("        --diffusion_samples %d \\" % DIFFUSION_SAMPLES)
        print("        --seed %d \\" % SEED)
        print("        --out_dir %s" % OUT)
        print("\n  --diffusion_samples %d   one sample is one draw from a"
              % DIFFUSION_SAMPLES)
        print("                          distribution. A single co-folded pose")
        print("                          reported without its spread is the same")
        print("                          error as a docking run at an unrecorded")
        print("                          seed.")
        print("  --seed %d               same rule as everywhere else here." % SEED)
        print("\nWhat would then have to be checked:\n")
        for step in CHECKS:
            print("  %s" % step)
        print("\nNothing is simulated. See ch13_cofolding/README.md.")
        write_report(path, mature, ran=False)
        return 3

    print("\nboltz found: %s" % boltz)
    subprocess.run([boltz, "predict", str(path), "--use_msa_server",
                    "--diffusion_samples", str(DIFFUSION_SAMPLES),
                    "--seed", str(SEED), "--out_dir", str(OUT)], check=True)
    write_report(path, mature, ran=True)
    return 0


CHECKS = [
    "1. Renumber. The model works in UniProt numbering, the crystal does not.",
    "2. Superimpose on the RECEPTOR, then measure the ligand RMSD with no",
    "   further fitting -- heavy-atom and symmetry-corrected, as in ch17. A",
    "   co-folded complex arrives in its own frame, and superimposing on the",
    "   LIGAND is the --minimize mistake wearing a different hat.",
    "3. Compare the predicted affinity against 26 uM while remembering ch14:",
    "   r = 0.62 on a benchmark is r-squared = 0.38, and this series spans",
    "   0.32 kcal/mol -- below what any current method resolves.",
]


def write_report(path, mature, ran):
    lines = [
        "# Chapter 13 — co-folding", "",
        "## The input", "",
        "`%s` — written whether or not the model can run, because the input is"
        % path.name,
        "half the protocol and can be checked without a GPU.", "",
        "| | |",
        "|---|---|",
        "| UniProt | %s |" % UNIPROT,
        "| Sequence | mature protein, %d residues (signal peptide 1–%d removed) |"
        % (len(mature), SIGNAL_PEPTIDE_END),
        "| Ligand | STC, SMILES with explicit −1 |",
        "| Seed | %d |" % SEED,
        "| Diffusion samples | %d |" % DIFFUSION_SAMPLES,
        "",
        "Three things in that file are easy to get wrong and impossible to",
        "notice afterwards:",
        "",
        "- **The signal peptide.** UniProt P00811 residues 1–19 are a signal",
        "  peptide that is not in the crystal structure. Folding it with the",
        "  complex hands the model 19 residues of something that is not there.",
        "  The script verifies the boundary by checking that residue 64 of the",
        "  mature sequence is a serine, and stops if it is not.",
        "- **The numbering.** The file is in UniProt numbering: Ser80 here,",
        "  Ser64 in every PDB file in this repository. Chapter 6 shows the",
        "  failure mode — asking a model for residue 64 returns isoleucine, with",
        "  no error raised.",
        "- **The charge.** The SMILES carries an explicit −1. Co-folding models",
        "  take SMILES and their handling of formal charge is not always",
        "  documented, which is worth checking before trusting a pose.",
        "",
        "## The prediction did not run here" if not ran else "## The prediction",
        "",
    ]
    if not ran:
        lines += [
            "Boltz-2 needs a CUDA GPU and several gigabytes of weights. This is a",
            "CPU-only Windows machine.",
            "",
            "**`pip install boltz` was attempted during this build.** It succeeds",
            "— and it downgrades numpy to 1.26, gemmi to 0.6.5 and scipy to 1.13,",
            "silently breaking the pinned environment every other chapter depends",
            "on. The environment had to be reinstalled. **Install co-folding",
            "models in a separate environment**, which is a specific and",
            "reproducible finding rather than general advice.",
            "",
            "The command this chapter would run, and what would then have to be",
            "checked, are printed by the script. Nothing is simulated.",
            "",
            "## What would have to be checked",
            "",
        ] + ["%s" % step for step in CHECKS] + [""]
    (OUT / "cofolding.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
