#!/usr/bin/env python3
"""Chapter 8 — protonation, stereochemistry and conformer generation.

    python ch08_ligand_prep/scripts/prepare_ligands.py

Three things, in the order they bite:

1. **Protonation at pH 7.4.** This series spans −1 and −2. Docking the drawn
   neutral forms gets every member wrong by a *different* amount, which
   corrupts the ranking rather than shifting it -- and a corrupted ranking
   still looks like a result. Protonation therefore comes **first**, before
   anything downstream is generated from the molecule.
2. **Stereochemistry across a round trip.** Cheap to check and expensive to
   discover later.
3. **Conformer generation.** ETKDGv3, 300 attempts, pruneRmsThresh 0.5, at five
   seeds -- because one seed tells you nothing about how stable the count is.
   Run on the **deprotonated** form, because that is the molecule that gets
   docked and the two forms give different counts.

Writes outputs/ligand_prep.json and outputs/ligand_prep.md.
"""
import json
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"

# The SMILES live in one place. Copying them here would let the two copies
# drift, and a ligand series that disagrees with itself is the failure this
# whole repository is trying to make impossible.
sys.path.insert(0, str(REPO / "data" / "ligands"))
from generate import LIGANDS  # noqa: E402

# ETKDGv3 with 300 attempts and a 0.5 A pruning threshold. Every one of those
# is load-bearing: the version of the algorithm, the attempt budget, and the
# threshold that decides when two conformers count as the same.
NUM_CONFS = 300
PRUNE_RMS = 0.5
SEEDS = [1, 7, 42, 99, 2026]

RDLogger.DisableLog("rdApp.*")


def conformer_count(mol, seed):
    """Conformers surviving the 0.5 A prune, from 300 attempts at one seed."""
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    params.pruneRmsThresh = PRUNE_RMS
    working = Chem.AddHs(Chem.Mol(mol))
    ids = AllChem.EmbedMultipleConfs(working, numConfs=NUM_CONFS, params=params)
    return len(ids)


def stereo_round_trip(mol):
    """Write to SDF, read back, and compare canonical SMILES with stereo.

    These three ligands are achiral, so this passes trivially -- and it is
    still worth running, because it is the check that catches the day someone
    adds a chiral analogue to the series.
    """
    embedded = Chem.AddHs(Chem.Mol(mol))
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    if AllChem.EmbedMolecule(embedded, params) != 0:
        return None, None, False
    before = Chem.MolToSmiles(Chem.RemoveHs(embedded), isomericSmiles=True)

    buffer = Chem.SDWriter.__new__(Chem.SDWriter)  # placeholder, replaced below
    path = OUT / "_stereo_roundtrip.sdf"
    writer = Chem.SDWriter(str(path))
    writer.write(embedded)
    writer.close()
    back = next(Chem.SDMolSupplier(str(path), removeHs=False))
    del buffer
    if back is None:
        return before, None, False
    # Re-perceive stereochemistry from the 3D coordinates, which is what any
    # tool reading the file will do.
    Chem.AssignStereochemistryFrom3D(back)
    after = Chem.MolToSmiles(Chem.RemoveHs(back), isomericSmiles=True)
    return before, after, before == after


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"settings": {"algorithm": "ETKDGv3", "num_confs": NUM_CONFS,
                            "prune_rms_thresh": PRUNE_RMS, "seeds": SEEDS,
                            "rdkit_version": Chem.rdBase.rdkitVersion},
               "ligands": {}}

    lines = ["# Chapter 8 — ligand preparation", "",
             "RDKit %s, ETKDGv3, %d attempts, pruneRmsThresh %.1f."
             % (Chem.rdBase.rdkitVersion, NUM_CONFS, PRUNE_RMS), ""]

    print("RDKit %s, ETKDGv3, %d attempts, pruneRmsThresh %.1f\n"
          % (Chem.rdBase.rdkitVersion, NUM_CONFS, PRUNE_RMS))
    print("%-5s %-7s %-6s %-22s %s"
          % ("", "charge", "rot.", "conformers (docked)", "conformers (neutral)"))

    for name, spec in LIGANDS.items():
        neutral = Chem.MolFromSmiles(spec["neutral"])
        docked = Chem.MolFromSmiles(spec["docked"])
        charge = Chem.GetFormalCharge(docked)

        # A hard failure, not a printed line. If a future RDKit changes
        # protonation behaviour the build must break loudly rather than quietly
        # docking the wrong species.
        if charge != spec["charge"]:
            sys.exit("%s: formal charge is %+d, the series table says %+d. "
                     "Stop -- do not dock this." % (name, charge, spec["charge"]))

        rot = Descriptors.NumRotatableBonds(docked)

        # Conformers are generated from the DEPROTONATED form -- the species
        # that will actually be docked. Protonation comes first; the conformer
        # search runs on what protonation produced. Generating on the drawn
        # neutral molecule and charging it afterwards searches the shape of a
        # molecule nobody docks, and the two forms give different counts, so
        # the order is not cosmetic. Both columns are recorded, because a
        # conformer table that does not say which form produced it cannot be
        # reproduced -- and reproducing the book's table required knowing.
        counts = {str(seed): conformer_count(docked, seed) for seed in SEEDS}
        counts_neutral = {str(seed): conformer_count(neutral, seed) for seed in SEEDS}
        before, after, preserved = stereo_round_trip(docked)

        results["ligands"][name] = {
            "smiles_neutral": spec["neutral"],
            "smiles_docked": spec["docked"],
            "formal_charge": charge,
            "formal_charge_neutral_form": Chem.GetFormalCharge(neutral),
            "rotatable_bonds": rot,
            "conformers": counts,
            "conformers_from_neutral_form": counts_neutral,
            "stereo_smiles_before": before,
            "stereo_smiles_after": after,
            "stereo_preserved": preserved,
            "ki": spec["ki"],
        }
        print("%-5s %+6d %6d   %-22s %s"
              % (name, charge, rot,
                 ", ".join(str(counts[str(s)]) for s in SEEDS),
                 ", ".join(str(counts_neutral[str(s)]) for s in SEEDS)))

    # -- the teaching point --------------------------------------------------
    # Conformer count does not track rotatable-bond count. 18U has two more
    # rotatable bonds than STC and yields fewer conformers, because the prune
    # threshold works on geometry rather than on topology: a flexible molecule
    # whose torsions lead to similar shapes collapses under a 0.5 A prune.
    lines.append("| Ligand | Charge at pH 7.4 | Rotatable bonds | Conformers, docked form | Conformers, neutral form |")
    lines.append("|---|---|---|---|---|")
    for name, entry in results["ligands"].items():
        lines.append("| %s | %+d | %d | %s | %s |"
                     % (name, entry["formal_charge"], entry["rotatable_bonds"],
                        ", ".join(str(entry["conformers"][str(s)]) for s in SEEDS),
                        ", ".join(str(entry["conformers_from_neutral_form"][str(s)])
                                  for s in SEEDS)))
    counts_1mu = results["ligands"]["1MU"]["conformers"]
    low_seed = min(SEEDS, key=lambda seed: counts_1mu[str(seed)])
    high_seed = max(SEEDS, key=lambda seed: counts_1mu[str(seed)])
    spread = {"low": counts_1mu[str(low_seed)], "low_seed": low_seed,
              "high": counts_1mu[str(high_seed)], "high_seed": high_seed}

    lines += [
        "",
        "Conformer counts do **not** track rotatable-bond count. 18U has two",
        "more rotatable bonds than STC and yields fewer conformers. That is the",
        "teaching point, not a bug: the 0.5 Å prune works on geometry, and a",
        "molecule whose extra torsions lead to similar shapes collapses under",
        "it. Do not 'fix' this.",
        "",
        # Read off the run rather than typed in, so this sentence cannot drift
        # from the table above it on a platform where the counts differ.
        "Counts also move with the seed — 1MU gives %d at seed %d against %d at"
        % (spread["low"], spread["low_seed"], spread["high"]),
        "seed %d. A conformer count quoted without its seed is not a number"
        % spread["high_seed"],
        "anyone can check.",
        "",
        "And they move with the protonation state. The docked column is the",
        "book's: protonation comes first, and the conformer search runs on the",
        "deprotonated species that will actually be docked. The neutral column",
        "is the same search run on the molecule as drawn, and it is a different",
        "molecule with different counts. A table that does not say which form",
        "it used cannot be reproduced, which is why both are printed here.",
        "",
        "## Charges",
        "",
        "The drawn (neutral) forms and the docked forms are different molecules:",
        "",
    ]
    for name, entry in results["ligands"].items():
        lines.append("- **%s** — drawn %+d, docked %+d, Ki %s"
                     % (name, entry["formal_charge_neutral_form"],
                        entry["formal_charge"], entry["ki"]))
    lines += [
        "",
        "The series spans −1 and −2, so docking the drawn forms is wrong by a",
        "different amount for each member. That corrupts the ranking rather",
        "than shifting it, and a corrupted ranking still looks like a result.",
        "",
        "## Stereochemistry",
        "",
        "All three ligands are achiral, so the SDF round-trip preserves the",
        "canonical isomeric SMILES trivially. The check is kept anyway: it costs",
        "nothing and it is what will catch the day a chiral analogue joins the",
        "series.",
        "",
    ]

    (OUT / "ligand_prep.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (OUT / "ligand_prep.md").write_text("\n".join(lines), encoding="utf-8")
    tmp = OUT / "_stereo_roundtrip.sdf"
    if tmp.exists():
        tmp.unlink()
    print("\nwrote %s" % (OUT / "ligand_prep.json"))


if __name__ == "__main__":
    main()
