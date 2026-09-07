#!/usr/bin/env python3
"""Chapter 12 — the mechanics of a screen, and what it would cost.

    python ch12_screening/scripts/screen.py [--exhaustiveness 8]

Docks a small library into AmpC: the three known actives from this repository
plus a set of common drugs as decoys. Twenty compounds is far too few to
measure enrichment — and saying so precisely is part of the chapter, because
the top 1% of twenty compounds is a fifth of a compound.

What twenty compounds *can* do is exercise the parts of a screen that fail at
scale:

  * a compound that will not prepare, and what the pipeline does about it
  * per-compound cost, measured rather than guessed
  * extrapolation to a real library, with the assumption stated

Writes outputs/screen.json and outputs/screen.md.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
WORK = OUT / "work"
STRUCTURES = REPO / "data" / "structures"
LIGANDS = REPO / "data" / "ligands"

sys.path.insert(0, str(REPO / "scripts"))
from docking_common import dock, find_tool, find_vina, vina_version  # noqa: E402
import receptor_prep  # noqa: E402

RDLogger.DisableLog("rdApp.*")

CRYSTAL, CHAIN, PADDING = "1L2S", "B", 8.0
SEED = 42

# Decoys: well-known drugs, so every SMILES here is checkable against any
# reference. They are NOT property-matched to the actives, which is a real
# weakness and is the reason this screen cannot be used to judge a method --
# see the README.
DECOYS = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "paracetamol": "CC(=O)Nc1ccc(O)cc1",
    "naproxen": "COc1ccc2cc(ccc2c1)C(C)C(=O)O",
    "diclofenac": "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl",
    "salicylic_acid": "OC(=O)c1ccccc1O",
    "benzoic_acid": "OC(=O)c1ccccc1",
    "caffeine": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
    "sulfanilamide": "Nc1ccc(cc1)S(N)(=O)=O",
    "sulfamethoxazole": "Cc1cc(no1)NS(=O)(=O)c1ccc(N)cc1",
    "probenecid": "CCCN(CCC)S(=O)(=O)c1ccc(cc1)C(=O)O",
    "furosemide": "NS(=O)(=O)c1cc(C(=O)O)c(NCc2ccco2)cc1Cl",
    "indomethacin": "COc1ccc2c(c1)c(CC(=O)O)c(C)n2C(=O)c1ccc(Cl)cc1",
    "phenylbutazone": "CCCCC1C(=O)N(c2ccccc2)N(c2ccccc2)C1=O",
    "warfarin": "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O",
    "acetazolamide": "CC(=O)Nc1nnc(s1)S(N)(=O)=O",
    # A deliberately awkward entry: a metal salt with no organic ligand at all.
    # Real libraries contain rows like this and a screen has to survive them.
    "sodium_chloride": "[Na+].[Cl-]",
}
ACTIVES = ["STC", "18U", "1MU"]

# Library sizes to extrapolate to.
LIBRARY_SIZES = [10_000, 100_000, 1_000_000]
CORES_AVAILABLE = 4


def prepare_decoy(name, smiles):
    """Build a 3D conformer and a PDBQT. Returns None if the compound fails.

    A screen has to survive its own library. Failures are counted and named,
    not skipped quietly -- a screen that silently drops 8% of its input has an
    enrichment factor computed over a library nobody can reconstruct.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, "SMILES did not parse"
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = SEED
    if AllChem.EmbedMolecule(mol, params) != 0:
        return None, "no 3D conformer could be embedded"
    AllChem.MMFFOptimizeMolecule(mol)
    sdf = WORK / ("%s.sdf" % name)
    writer = Chem.SDWriter(str(sdf))
    writer.write(mol)
    writer.close()
    pdbqt = WORK / ("%s.pdbqt" % name)
    if pdbqt.exists():
        pdbqt.unlink()
    subprocess.run([find_tool("mk_prepare_ligand"), "-i", str(sdf), "-o", str(pdbqt)],
                   capture_output=True, text=True)
    if not pdbqt.exists():
        return None, "meeko wrote no PDBQT"
    return pdbqt, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exhaustiveness", type=int, default=8,
                    help="Vina's default is 8; screens usually stay there")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    path = STRUCTURES / ("%s.pdb" % CRYSTAL)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    atoms, _, _ = receptor_prep.parse(path)
    chosen, _copies = receptor_prep.select_copy(atoms, "STC", CHAIN)
    if chosen is None:
        sys.exit("%s: no catalytic STC copy in chain %s" % (CRYSTAL, CHAIN))
    centre, size, _ = receptor_prep.box_from_ligand(chosen["atoms"], PADDING)
    receptor_pdbqt, decisions = receptor_prep.prepare(path, CHAIN, WORK, "receptor")

    vina = find_vina()
    print("Vina: %s, seed %d, exhaustiveness %d"
          % (vina_version(vina), SEED, args.exhaustiveness))
    print("receptor %s chain %s, box %.1f x %.1f x %.1f\n"
          % (CRYSTAL, CHAIN, size[0], size[1], size[2]))

    library, failures = [], []
    for name in ACTIVES:
        source = LIGANDS / ("%s.sdf" % name)
        pdbqt = WORK / ("active_%s.pdbqt" % name)
        subprocess.run([find_tool("mk_prepare_ligand"), "-i", str(source),
                        "-o", str(pdbqt)], capture_output=True, text=True)
        if not pdbqt.exists():
            failures.append({"name": name, "reason": "meeko wrote no PDBQT"})
            continue
        mol = next(Chem.SDMolSupplier(str(source), removeHs=False))
        library.append({"name": name, "pdbqt": pdbqt, "active": True,
                        "mw": round(Descriptors.MolWt(Chem.RemoveHs(mol)), 1)})

    for name, smiles in DECOYS.items():
        pdbqt, reason = prepare_decoy(name, smiles)
        if pdbqt is None:
            failures.append({"name": name, "reason": reason, "smiles": smiles})
            continue
        library.append({"name": name, "pdbqt": pdbqt, "active": False,
                        "mw": round(Descriptors.MolWt(Chem.MolFromSmiles(smiles)), 1)})

    print("Library: %d compounds prepared, %d failed" % (len(library), len(failures)))
    for failure in failures:
        print("   FAILED %-18s %s" % (failure["name"], failure["reason"]))
    if failures:
        print("   Counted and named, not skipped. A screen that quietly drops")
        print("   part of its library computes enrichment over a set nobody")
        print("   can reconstruct.")

    print("\n%-20s %-9s %-9s %s" % ("compound", "MW", "affinity", "seconds"))
    started = time.perf_counter()
    for entry in library:
        modes, elapsed, _ = dock(receptor_pdbqt, entry["pdbqt"], centre, size,
                                 WORK / ("%s_pose.pdbqt" % entry["name"]),
                                 seed=SEED, exhaustiveness=args.exhaustiveness,
                                 vina=vina)
        entry["affinity"] = modes[0][1]
        entry["seconds"] = round(elapsed, 2)
        print("%-20s %-9.1f %-9.3f %.2f"
              % (entry["name"] + (" *" if entry["active"] else ""),
                 entry["mw"], entry["affinity"], elapsed))
    wall = time.perf_counter() - started

    ranked = sorted(library, key=lambda e: e["affinity"])
    print("\nRanked, best first:")
    for position, entry in enumerate(ranked, start=1):
        print("   %2d. %-20s %.3f%s"
              % (position, entry["name"], entry["affinity"],
                 "   <- known active" if entry["active"] else ""))

    active_ranks = [i for i, e in enumerate(ranked, start=1) if e["active"]]
    n_actives = len(active_ranks)
    print("\nThe %d known actives rank %s of %d."
          % (n_actives, ", ".join(str(r) for r in active_ranks), len(ranked)))

    # The honest statement about enrichment at this size.
    top_one_percent = len(ranked) * 0.01
    print("\nEnrichment at this size:")
    print("   the top 1%% of %d compounds is %.2f compounds." % (len(ranked),
                                                                 top_one_percent))
    print("   EF1% is not defined here, and any number reported for it would be")
    print("   an artefact of rounding. Chapter 18 is where enrichment metrics")
    print("   are measured, on 10,000 compounds.")

    per_compound = wall / max(len(library), 1)
    print("\nCost, measured: %.2f s per compound on %d cores."
          % (per_compound, CORES_AVAILABLE))
    print("%-14s %-16s %s" % ("library", "core-hours", "wall time on 100 cores"))
    extrapolation = {}
    for size_n in LIBRARY_SIZES:
        core_hours = per_compound * size_n * CORES_AVAILABLE / 3600
        extrapolation[size_n] = {"core_hours": round(core_hours, 1),
                                 "days_on_100_cores": round(core_hours / 100 / 24, 2)}
        print("%-14s %-16.1f %.2f days"
              % ("{:,}".format(size_n), core_hours, core_hours / 100 / 24))
    print("\nStraight-line extrapolation, which assumes every compound costs what")
    print("these did. Bigger and more flexible ligands cost more, so treat this")
    print("as a floor rather than an estimate.")

    payload = {
        "receptor": {"pdb_id": CRYSTAL, "chain": CHAIN, **decisions},
        "docking": {"seed": SEED, "exhaustiveness": args.exhaustiveness,
                    "program": vina_version(vina), "cores": CORES_AVAILABLE},
        "box": {"centre": [round(c, 3) for c in centre], "size": list(size)},
        "library_size": len(library),
        "failures": failures,
        "results": [{k: v for k, v in e.items() if k != "pdbqt"} for e in ranked],
        "active_ranks": active_ranks,
        "seconds_per_compound": round(per_compound, 2),
        "extrapolation": {str(k): v for k, v in extrapolation.items()},
        "ef1_is_defined": len(ranked) >= 100,
    }
    (OUT / "screen.json").write_text(json.dumps(payload, indent=2) + "\n",
                                     encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "screen.json"))


def write_report(payload):
    lines = [
        "# Chapter 12 — screening", "",
        "%d compounds into %s chain %s. %s, seed %d, exhaustiveness %d."
        % (payload["library_size"], payload["receptor"]["pdb_id"],
           payload["receptor"]["chain"], payload["docking"]["program"],
           payload["docking"]["seed"], payload["docking"]["exhaustiveness"]),
        "", "## The ranking", "",
        "| Rank | Compound | MW | Affinity | |",
        "|---|---|---|---|---|",
    ]
    for position, entry in enumerate(payload["results"], start=1):
        lines.append("| %d | %s | %.1f | %.3f | %s |"
                     % (position, entry["name"], entry["mw"], entry["affinity"],
                        "**known active**" if entry["active"] else ""))
    lines += [
        "",
        "The three known actives rank %s of %d."
        % (", ".join(str(r) for r in payload["active_ranks"]),
           payload["library_size"]),
        "",
        "## Enrichment is not defined at this size",
        "",
        "The top 1%% of %d compounds is %.2f compounds. **EF1%% cannot be**"
        % (payload["library_size"], payload["library_size"] * 0.01),
        "**computed here**, and any number reported for it would be an artefact",
        "of rounding. Chapter 18 measures enrichment properly, on 10,000",
        "compounds, and shows what the metric is and is not sensitive to.",
        "",
        "The decoys here are also **not property-matched** to the actives — they",
        "are common drugs, chosen so every SMILES is checkable against any",
        "reference. A screen whose decoys are lighter and less charged than its",
        "actives measures molecular weight, not binding.",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines += ["| Compound | Reason |", "|---|---|"]
        for failure in payload["failures"]:
            lines.append("| %s | %s |" % (failure["name"], failure["reason"]))
        lines += [
            "",
            "Named, not skipped. A screen that quietly drops part of its library",
            "reports an enrichment factor computed over a set nobody can",
            "reconstruct — and the dropped rows are rarely a random sample of the",
            "library.",
        ]
    else:
        lines.append("None — every compound prepared.")
    lines += [
        "", "## What it would cost", "",
        "%.2f s per compound, measured on %d cores."
        % (payload["seconds_per_compound"], payload["docking"]["cores"]),
        "",
        "| Library | Core-hours | Wall time on 100 cores |",
        "|---|---|---|",
    ]
    for size_n, entry in payload["extrapolation"].items():
        lines.append("| %s | %.1f | %.2f days |"
                     % ("{:,}".format(int(size_n)), entry["core_hours"],
                        entry["days_on_100_cores"]))
    lines += [
        "",
        "Straight-line extrapolation, which assumes every compound costs what",
        "these did. Bigger and more flexible ligands cost more, so this is a",
        "floor rather than an estimate — and it is the number that decides",
        "whether a screen happens, so it is worth measuring rather than guessing.",
        "",
    ]
    (OUT / "screen.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
