#!/usr/bin/env python3
"""Chapter 7 — where is the pocket, and what does getting it wrong cost?

    python ch07_pocket/scripts/define_pocket.py

Four ways to define the search box, docked with an identical protocol:

  ligand      centroid of the crystallographic ligand, 8 Å padding.
              The best case, and unavailable in any real project -- if you had
              the ligand's position you would not be docking.
  residues    centroid of the known binding-site residues. What you do when
              the site is known from the literature but no complex exists.
  catalytic   a fixed box on the catalytic serine alone. What you do when one
              residue is all the annotation gives you.
  blind       a box around the whole protein. What you do when you know
              nothing, and what it costs.

Each is scored the same way and its pose measured against the
crystallographic one, so the comparison is of box definitions and nothing else.

Writes outputs/pocket.json and outputs/pocket.md.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

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

CRYSTAL = "1L2S"
CHAIN = "B"
LIGAND = "STC"
SEED = 42
EXHAUSTIVENESS = 32
PADDING = 8.0

SITE_RESIDUES = ["64", "67", "119", "120", "150", "152", "221", "293",
                 "315", "316", "317", "318", "346", "349"]
CATALYTIC_BOX = 22.0     # Å cube on Ser64 OG: big enough for the ligand plus slack


def symmetry_rmsd(reference, pose):
    from spyrmsd import molecule, rmsd as spyrmsd_rmsd

    def load(mol):
        m = molecule.Molecule.from_rdkit(mol)
        m.strip()
        return m

    ref, target = load(reference), load(pose)
    return float(spyrmsd_rmsd.symmrmsd(
        ref.coordinates, target.coordinates,
        ref.atomicnums, target.atomicnums,
        ref.adjacency_matrix, target.adjacency_matrix,
        center=False, minimize=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    path = STRUCTURES / ("%s.pdb" % CRYSTAL)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    atoms, _, _ = receptor_prep.parse(path)

    copies = [c for c in receptor_prep.ligand_copies(atoms, LIGAND)
              if c["in_site"] and c["chain"] == CHAIN]
    lig_atoms = copies[0]["atoms"]
    lig_centre, lig_size, _ = receptor_prep.box_from_ligand(lig_atoms, PADDING)

    protein = [a for a in atoms if a["rec"] == "ATOM" and a["chain"] == CHAIN]
    coords = np.array([a["xyz"] for a in protein])

    site_atoms = [a for a in protein if a["seq"] in SITE_RESIDUES]
    site_coords = np.array([a["xyz"] for a in site_atoms])
    site_centre = tuple(site_coords.mean(axis=0))
    site_size = tuple(round(float(v), 2) for v in
                      (site_coords.max(axis=0) - site_coords.min(axis=0) + 2 * PADDING))

    catalytic = [a for a in protein
                 if (a["res"], a["seq"], a["name"]) == receptor_prep.CATALYTIC][0]

    blind_centre = tuple(coords.mean(axis=0))
    blind_size = tuple(round(float(v), 2) for v in
                       (coords.max(axis=0) - coords.min(axis=0) + 4.0))

    definitions = {
        "ligand": {"centre": lig_centre, "size": lig_size,
                   "what": "centroid of the crystallographic ligand, %.0f A padding" % PADDING},
        "residues": {"centre": site_centre, "size": site_size,
                     "what": "centroid of %d known site residues, %.0f A padding"
                             % (len(SITE_RESIDUES), PADDING)},
        "catalytic": {"centre": catalytic["xyz"], "size": (CATALYTIC_BOX,) * 3,
                      "what": "%.0f A cube on Ser64 OG alone" % CATALYTIC_BOX},
        "blind": {"centre": blind_centre, "size": blind_size,
                  "what": "the whole chain"},
    }

    receptor_pdbqt, decisions = receptor_prep.prepare(path, CHAIN, WORK, "receptor")
    ligand_pdbqt = WORK / ("%s.pdbqt" % LIGAND)
    subprocess.run([find_tool("mk_prepare_ligand"),
                    "-i", str(LIGANDS / ("%s.sdf" % LIGAND)), "-o", str(ligand_pdbqt)],
                   capture_output=True, text=True)
    if not ligand_pdbqt.exists():
        sys.exit("ligand preparation failed")

    fragment = WORK / "crystal_ligand.pdb"
    fragment.write_text("\n".join(a["line"] for a in lig_atoms) + "\nEND\n",
                        encoding="utf-8")
    template = Chem.MolToSmiles(Chem.RemoveHs(next(Chem.SDMolSupplier(
        str(LIGANDS / ("%s.sdf" % LIGAND)), removeHs=False))))
    reference = Chem.RemoveHs(AllChem.AssignBondOrdersFromTemplate(
        Chem.MolFromSmiles(template),
        Chem.MolFromPDBFile(str(fragment), removeHs=True, sanitize=False)))

    vina = find_vina()
    print("Vina: %s, seed %d, exhaustiveness %d\n"
          % (vina_version(vina), SEED, EXHAUSTIVENESS))
    print("%-11s %-26s %-11s %-9s %-9s %-6s %s"
          % ("definition", "box (A)", "volume", "affinity", "RMSD", "in site", "seconds"))

    results = {}
    for name, spec in definitions.items():
        centre, size = spec["centre"], spec["size"]
        volume = size[0] * size[1] * size[2]
        pose = WORK / ("%s_pose.pdbqt" % name)
        modes, elapsed, _ = dock(receptor_pdbqt, ligand_pdbqt, centre, size, pose,
                                 seed=SEED, exhaustiveness=EXHAUSTIVENESS, vina=vina,
                                 log_path=OUT / "logs" / ("%s.log" % name))
        sdf = WORK / ("%s_pose.sdf" % name)
        subprocess.run([find_tool("mk_export"), str(pose), "-s", str(sdf)],
                       capture_output=True, text=True)
        poses = [m for m in Chem.SDMolSupplier(str(sdf), removeHs=True) if m]
        rmsd = symmetry_rmsd(reference, poses[0]) if poses else None
        best = min((symmetry_rmsd(reference, p) for p in poses), default=None)

        # Mode 1 landing correctly is not the whole story. A large box fills
        # the remaining modes with surface sites, and a reader looking at a
        # result list has to sort real poses from places the ligand merely fit.
        true_centre = np.array(lig_centre)
        in_site = 0
        for mol in poses:
            centroid = np.array(mol.GetConformer().GetPositions()).mean(axis=0)
            if np.linalg.norm(centroid - true_centre) < 5.0:
                in_site += 1

        # Distance from this box centre to the true ligand centroid, which is
        # the thing each definition is trying to estimate without being told.
        offset = float(np.linalg.norm(np.array(centre) - np.array(lig_centre)))

        results[name] = {
            "what": spec["what"],
            "centre": [round(float(c), 3) for c in centre],
            "size": [round(float(s), 2) for s in size],
            "volume_A3": round(volume, 0),
            "offset_from_true_centre": round(offset, 2),
            "best_affinity": modes[0][1],
            "rmsd": round(rmsd, 3) if rmsd is not None else None,
            "rmsd_best_mode": round(best, 3) if best is not None else None,
            "seconds": round(elapsed, 1),
            "modes": len(poses),
            "modes_in_the_true_site": in_site,
        }
        print("%-11s %-26s %-11s %-9.3f %-9s %-6s %.1f"
              % (name, "%.1f x %.1f x %.1f" % tuple(size),
                 "%.0f" % volume, modes[0][1],
                 "%.3f" % rmsd if rmsd is not None else "-",
                 "%d/%d" % (in_site, len(poses)), elapsed))

    print("\nThe box centre each definition arrived at, against the true one:")
    for name, entry in results.items():
        print("   %-11s %6.2f A off" % (name, entry["offset_from_true_centre"]))

    blind, ligand = results["blind"], results["ligand"]
    print("\nBlind docking is %.0fx the volume and %.1fx the time of the ligand box,"
          % (blind["volume_A3"] / ligand["volume_A3"],
             blind["seconds"] / max(ligand["seconds"], 0.1)))
    print("for a pose %.3f A from the crystallographic one against %.3f A."
          % (blind["rmsd"], ligand["rmsd"]))
    print("\nModes landing in the true site: %s"
          % ", ".join("%s %d/%d" % (n, results[n]["modes_in_the_true_site"],
                                    results[n]["modes"])
                      for n in ("ligand", "residues", "catalytic", "blind")))

    # State the result, whatever it turns out to be. The expected story is that
    # a big box degrades the answer. On this system it does not, and writing
    # the expected story anyway would be the exact failure this book is about.
    spread = (max(e["rmsd"] for e in results.values())
              - min(e["rmsd"] for e in results.values()))
    if spread < 0.5:
        print("\nAll four definitions put the top pose within %.2f A of each other,"
              % spread)
        print("and %d of 9 modes land in the true site even for the blind box."
              % blind["modes_in_the_true_site"])
        print("\nOn THIS system the box hardly matters. AmpC has one dominant")
        print("pocket and STC is a good binder for it. That is a fact about the")
        print("system, not a general licence: a protein with several pockets, or")
        print("a weaker ligand, is where a careless box costs you the answer.")
        print("\nWhat the large box does cost here is grid volume -- %.0fx it, for"
              % (blind["volume_A3"] / ligand["volume_A3"]))
        print("%.1fx the wall time. That is the part that scales into a screen."
              % (blind["seconds"] / max(ligand["seconds"], 0.1)))
    else:
        print("\nThe box definition moves the top pose by up to %.2f A." % spread)

    payload = {"crystal": CRYSTAL, "chain": CHAIN, "ligand": LIGAND,
               "docking": {"seed": SEED, "exhaustiveness": EXHAUSTIVENESS,
                           "program": vina_version(vina)},
               "receptor": decisions,
               "true_centre": [round(float(c), 3) for c in lig_centre],
               "definitions": results}
    (OUT / "pocket.json").write_text(json.dumps(payload, indent=2) + "\n",
                                     encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "pocket.json"))


def write_report(payload):
    results = payload["definitions"]
    lines = [
        "# Chapter 7 — defining the pocket", "",
        "Four box definitions, one protocol: %s, seed %d, exhaustiveness %d."
        % (payload["docking"]["program"], payload["docking"]["seed"],
           payload["docking"]["exhaustiveness"]),
        "",
        "| Definition | Box (Å) | Volume (Å³) | Centre off by | Affinity | RMSD | Modes in site | Seconds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in ("ligand", "residues", "catalytic", "blind"):
        e = results[name]
        lines.append("| **%s** | %.1f × %.1f × %.1f | %.0f | %.2f Å | %.3f | %.3f Å | %d/%d | %.1f |"
                     % (name, e["size"][0], e["size"][1], e["size"][2],
                        e["volume_A3"], e["offset_from_true_centre"],
                        e["best_affinity"], e["rmsd"],
                        e["modes_in_the_true_site"], e["modes"], e["seconds"]))
    lines += [
        "",
        "What each definition means:",
        "",
    ]
    for name in ("ligand", "residues", "catalytic", "blind"):
        lines.append("- **%s** — %s" % (name, results[name]["what"]))
    lines += [
        "",
        "The `ligand` row is the best case and is **not available in any real",
        "project**: if you knew where the ligand sat you would not be docking.",
        "It is here as the ceiling the others are measured against.",
        "",
    ]
    (OUT / "pocket.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
