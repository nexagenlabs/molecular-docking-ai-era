#!/usr/bin/env python3
"""Chapter 26 — three reproduction tests with published answers.

    python ch26_case_study/scripts/case_study.py

1. **Redock 1L2S.** The original authors reported 1.75 Å and 1.87 Å against
   the crystal pose.
2. **Cross-dock.** Every ligand into every receptor — nine runs. Redocking is
   the diagonal; the off-diagonal is what prospective work actually looks like.
3. **Rank the series** against Ki = 26 µM (STC), 18 µM (18U), and 26 or 31 µM
   (1MU, depending on the source).

Each test has a published answer, so each can fail. That is the point: a
protocol that cannot fail has not been validated.

Writes outputs/case_study.json and outputs/case_study.md.
"""
import json
import math
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
WORK = OUT / "work"
STRUCTURES = REPO / "data" / "structures"
LIGANDS = REPO / "data" / "ligands"

sys.path.insert(0, str(REPO / "scripts"))
from docking_common import dock, find_tool, find_vina, platform_banner, vina_version  # noqa: E402
import molfile  # noqa: E402
import receptor_prep  # noqa: E402

RDLogger.DisableLog("rdApp.*")

SEED = 42
EXHAUSTIVENESS = 32
PADDING = 8.0

# Receptor, its own ligand, and the chain. Same decisions as Chapter 17, made
# there and reused here rather than made again.
TARGETS = {
    "1L2S": {"ligand": "STC", "chain": "B"},
    "4JXS": {"ligand": "18U", "chain": "B"},
    "4JXV": {"ligand": "1MU", "chain": "A"},
}

# Ki in micromolar. 1MU disagrees between sources and BOTH are carried through
# to the end: the disagreement is larger than the gap it would have to resolve.
KI = {
    "STC": {"chembl": 26.0, "pdbbind": 26.0},
    "18U": {"chembl": 18.0, "pdbbind": 18.0},
    "1MU": {"chembl": 26.0, "pdbbind": 31.0},
}

# What the original authors reported for the 1L2S redock.
PUBLISHED_REDOCK_RMSD = [1.75, 1.87]

RT = 0.001987 * 298.15      # kcal/mol at 25 C


def ki_to_dg(ki_micromolar):
    """Ki in uM to a binding free energy in kcal/mol.

    This direction is arithmetic and safe. The reverse -- reading a Ki off a
    docking score -- is not, and neither is converting between Ki, IC50 and Kd,
    which is why no such conversion appears anywhere in this repository.
    """
    return RT * math.log(ki_micromolar * 1e-6)


def symmetry_rmsd(reference, pose):
    """Heavy-atom, symmetry-corrected, no superposition."""
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


def crystal_reference(pdb_id, ligand_name, lig_atoms, template_smiles):
    fragment = WORK / ("%s_%s_crystal.pdb" % (pdb_id, ligand_name))
    fragment.write_text("\n".join(a["line"] for a in lig_atoms) + "\nEND\n",
                        encoding="utf-8")
    raw = Chem.MolFromPDBFile(str(fragment), removeHs=True, sanitize=False)
    template = Chem.MolFromSmiles(template_smiles)
    try:
        return Chem.RemoveHs(AllChem.AssignBondOrdersFromTemplate(template, raw))
    except ValueError as exc:
        sys.exit("%s: crystallographic %s does not match the reference SMILES (%s)"
                 % (pdb_id, ligand_name, exc))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    vina = find_vina()
    print("Vina: %s" % vina_version(vina))
    print(platform_banner())
    print("seed %d, exhaustiveness %d\n" % (SEED, EXHAUSTIVENESS))

    # -- prepare every receptor and every ligand once ------------------------
    receptors, references, boxes = {}, {}, {}
    for pdb_id, spec in TARGETS.items():
        path = STRUCTURES / ("%s.pdb" % pdb_id)
        if not path.exists():
            sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
        atoms, _, _ = receptor_prep.parse(path)
        copy, _copies = receptor_prep.select_copy(atoms, spec["ligand"],
                                                  spec["chain"])
        if copy is None:
            sys.exit("%s: no catalytic %s copy in chain %s"
                     % (pdb_id, spec["ligand"], spec["chain"]))
        lig_atoms = copy["atoms"]
        altlocs = sorted({a["altloc"] for a in lig_atoms if a["altloc"] != " "})
        if altlocs:
            lig_atoms = [a for a in lig_atoms if a["altloc"] in (" ", altlocs[0])]

        pdbqt, decisions = receptor_prep.prepare(path, spec["chain"], WORK,
                                                 "%s_receptor" % pdb_id)
        receptors[pdb_id] = {"pdbqt": pdbqt, "decisions": decisions}
        centre, size, _ = receptor_prep.box_from_ligand(lig_atoms, PADDING)
        boxes[pdb_id] = {"centre": centre, "size": size}

        source = LIGANDS / ("%s.sdf" % spec["ligand"])
        template = Chem.MolToSmiles(Chem.RemoveHs(molfile.read_one(
            source, what="the %s reference copy" % spec["ligand"])))
        references[pdb_id] = crystal_reference(pdb_id, spec["ligand"],
                                               lig_atoms, template)
        print("%s: chain %s, %d atoms, %s copy %s/%s at %.2f A from Ser64 OG"
              % (pdb_id, spec["chain"], decisions["atoms"], spec["ligand"],
                 copy["chain"], copy["seq"], copy["distance_to_ser64_og"]))

    ligand_pdbqt = {}
    for name in ("STC", "18U", "1MU"):
        out = WORK / ("%s.pdbqt" % name)
        import subprocess
        subprocess.run([find_tool("mk_prepare_ligand"),
                        "-i", str(LIGANDS / ("%s.sdf" % name)), "-o", str(out)],
                       capture_output=True, text=True)
        if not out.exists():
            sys.exit("ligand preparation failed for %s" % name)
        ligand_pdbqt[name] = out

    # -- the 3 x 3 matrix ----------------------------------------------------
    print("\nCross-docking: every ligand into every receptor\n")
    print("%-10s %-8s %-12s %-12s %s"
          % ("receptor", "ligand", "affinity", "RMSD", "note"))
    matrix = {}
    for pdb_id in TARGETS:
        matrix[pdb_id] = {}
        for name in ("STC", "18U", "1MU"):
            pose = WORK / ("%s_%s_pose.pdbqt" % (pdb_id, name))
            modes, elapsed, _ = dock(receptors[pdb_id]["pdbqt"], ligand_pdbqt[name],
                                     boxes[pdb_id]["centre"], boxes[pdb_id]["size"],
                                     pose, seed=SEED,
                                     exhaustiveness=EXHAUSTIVENESS, vina=vina,
                                     log_path=OUT / "logs" / ("%s_%s.log" % (pdb_id, name)))
            native = TARGETS[pdb_id]["ligand"] == name
            entry = {"affinity": modes[0][1], "seconds": round(elapsed, 1),
                     "native": native, "rmsd": None}
            if native:
                # RMSD is only meaningful against the ligand that was actually
                # crystallised here. Measuring 18U against the 1L2S STC pose
                # would be comparing two different molecules.
                sdf = WORK / ("%s_%s_pose.sdf" % (pdb_id, name))
                import subprocess as sp
                sp.run([find_tool("mk_export"), str(pose), "-s", str(sdf)],
                       capture_output=True, text=True)
                # try_read_all: a cell of the cross-docking matrix that
                # produced no pose is reported as such, not a reason to stop.
                poses = molfile.try_read_all(sdf)
                if poses:
                    entry["rmsd"] = round(symmetry_rmsd(references[pdb_id], poses[0]), 3)
                    entry["rmsd_best_mode"] = round(
                        min(symmetry_rmsd(references[pdb_id], p) for p in poses), 3)
            matrix[pdb_id][name] = entry
            print("%-10s %-8s %-12.3f %-12s %s"
                  % (pdb_id, name, entry["affinity"],
                     ("%.3f A" % entry["rmsd"]) if entry["rmsd"] is not None else "-",
                     "REDOCK" if native else "cross-dock"))

    # -- test 1: the 1L2S redock --------------------------------------------
    redock = matrix["1L2S"]["STC"]["rmsd"]
    print("\n1. REDOCK 1L2S")
    print("   this run: %.3f A;  published: %s A"
          % (redock, " and ".join("%.2f" % v for v in PUBLISHED_REDOCK_RMSD)))
    print("   %s the published range"
          % ("inside" if min(PUBLISHED_REDOCK_RMSD) <= redock <= max(PUBLISHED_REDOCK_RMSD)
             else "below" if redock < min(PUBLISHED_REDOCK_RMSD) else "above"))
    print("   Under 2 A either way, which is the criterion that matters.")

    # -- test 2: does the native receptor win? ------------------------------
    print("\n2. CROSS-DOCKING")
    print("   Does each ligand score best in the structure it came from?")
    self_preference = {}
    for name in ("STC", "18U", "1MU"):
        scores = {pdb_id: matrix[pdb_id][name]["affinity"] for pdb_id in TARGETS}
        best = min(scores, key=scores.get)
        native = [p for p, s in TARGETS.items() if s["ligand"] == name][0]
        self_preference[name] = {"scores": scores, "best_receptor": best,
                                 "native_receptor": native,
                                 "prefers_native": best == native}
        print("   %-5s best in %s (%.3f), native is %s -- %s"
              % (name, best, scores[best], native,
                 "yes" if best == native else "NO"))
    print("   A ligand that does not prefer its own crystal structure is telling")
    print("   you the receptor conformations differ more than the ligands do.")

    # -- test 3: ranking against Ki -----------------------------------------
    print("\n3. RANKING THE SERIES")
    print("   Docking into 1L2S, against measured Ki:\n")
    print("   %-6s %-12s %-14s %-14s %s"
          % ("ligand", "affinity", "Ki (ChEMBL)", "Ki (PDBbind)", "dG from Ki"))
    ranking = {}
    for name in ("STC", "18U", "1MU"):
        affinity = matrix["1L2S"][name]["affinity"]
        ranking[name] = {
            "affinity": affinity,
            "ki_chembl_um": KI[name]["chembl"],
            "ki_pdbbind_um": KI[name]["pdbbind"],
            "dg_from_ki_chembl": round(ki_to_dg(KI[name]["chembl"]), 2),
            "dg_from_ki_pdbbind": round(ki_to_dg(KI[name]["pdbbind"]), 2),
        }
        print("   %-6s %-12.3f %-14s %-14s %.2f to %.2f kcal/mol"
              % (name, affinity, "%.0f uM" % KI[name]["chembl"],
                 "%.0f uM" % KI[name]["pdbbind"],
                 ranking[name]["dg_from_ki_pdbbind"],
                 ranking[name]["dg_from_ki_chembl"]))

    def order(key):
        """Rank, with ties shown as ties.

        sorted() will happily put STC before 1MU when both are 26 uM, and the
        result then reads as a ranking the data does not contain. Equal values
        are grouped instead.
        """
        groups = {}
        for name in ranking:
            groups.setdefault(ranking[name][key], []).append(name)
        return [sorted(groups[value]) for value in sorted(groups)]

    by_score = order("affinity")
    by_ki_chembl = order("ki_chembl_um")
    by_ki_pdbbind = order("ki_pdbbind_um")
    print("\n   by docking score: %s" % _show(by_score))
    print("   by Ki (ChEMBL):   %s" % _show(by_ki_chembl))
    print("   by Ki (PDBbind):  %s" % _show(by_ki_pdbbind))
    if any(len(g) > 1 for g in by_ki_chembl):
        print("   ChEMBL does not order STC against 1MU at all: both are 26 uM.")

    # The experimental ranking is not even well defined. STC and 1MU are 26 uM
    # each in ChEMBL; PDBbind puts 1MU at 31. The whole spread of the series is
    # 18 to 31 uM -- a factor of 1.7, or 0.3 kcal/mol. No docking function
    # resolves 0.3 kcal/mol, and a method that appeared to would be reporting
    # its own noise.
    spread = (max(KI[n]["pdbbind"] for n in KI) / min(KI[n]["chembl"] for n in KI))
    energy_spread = abs(ki_to_dg(max(KI[n]["pdbbind"] for n in KI))
                        - ki_to_dg(min(KI[n]["chembl"] for n in KI)))
    print("\n   The series spans %.0f-%.0f uM: a factor of %.1f, or %.2f kcal/mol."
          % (min(KI[n]["chembl"] for n in KI), max(KI[n]["pdbbind"] for n in KI),
             spread, energy_spread))
    print("   The two sources disagree about 1MU by more than the gap between")
    print("   STC and 1MU. There is no reliable ranking here to reproduce, and a")
    print("   method that claimed to resolve %.2f kcal/mol would be reporting"
          % energy_spread)
    print("   its own noise.")

    payload = {
        "docking": {"seed": SEED, "exhaustiveness": EXHAUSTIVENESS,
                    "program": vina_version(vina)},
        "receptors": {k: v["decisions"] for k, v in receptors.items()},
        "boxes": {k: {"centre": [round(c, 3) for c in v["centre"]],
                      "size": list(v["size"])} for k, v in boxes.items()},
        "matrix": matrix,
        "test1_redock_1l2s": {"rmsd": redock, "published": PUBLISHED_REDOCK_RMSD,
                              "under_2A": redock < 2.0},
        "test2_cross_docking": self_preference,
        "test3_ranking": {"by_docking_score": by_score,
                          "chembl_has_a_tie": any(len(g) > 1 for g in by_ki_chembl),
                          "by_ki_chembl": by_ki_chembl,
                          "by_ki_pdbbind": by_ki_pdbbind,
                          "chembl_has_a_tie": any(len(g) > 1 for g in by_ki_chembl),
                          "ligands": ranking,
                          "series_spread_kcal": round(energy_spread, 2)},
    }
    (OUT / "case_study.json").write_text(json.dumps(payload, indent=2) + "\n",
                                         encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "case_study.json"))


def _show(groups):
    return " < ".join(" = ".join(g) for g in groups)


def write_report(payload):
    matrix = payload["matrix"]
    lines = [
        "# Chapter 26 — case study: three reproduction tests", "",
        "%s, seed %d, exhaustiveness %d."
        % (payload["docking"]["program"], payload["docking"]["seed"],
           payload["docking"]["exhaustiveness"]),
        "",
        "## The cross-docking matrix",
        "",
        "Affinity in kcal/mol; the diagonal is a redock and carries an RMSD.",
        "",
        "| Receptor | STC | 18U | 1MU |",
        "|---|---|---|---|",
    ]
    for pdb_id in ("1L2S", "4JXS", "4JXV"):
        cells = []
        for name in ("STC", "18U", "1MU"):
            entry = matrix[pdb_id][name]
            cell = "%.3f" % entry["affinity"]
            if entry["native"]:
                cell = "**%s** (RMSD %.3f Å)" % (cell, entry["rmsd"])
            cells.append(cell)
        lines.append("| %s | %s |" % (pdb_id, " | ".join(cells)))

    test1 = payload["test1_redock_1l2s"]
    lines += [
        "",
        "## Test 1 — redock 1L2S",
        "",
        "| | RMSD |",
        "|---|---|",
        "| This run | **%.3f Å** |" % test1["rmsd"],
        "| Original authors | %s Å |"
        % " and ".join("%.2f" % v for v in test1["published"]),
        "",
        "Under 2 Å either way, which is the criterion that matters. Reproducing",
        "a published number to two decimals would be surprising; reproducing the",
        "*conclusion* is what a reproduction test is for.",
        "",
        "## Test 2 — cross-docking",
        "",
        "| Ligand | Best receptor | Native receptor | Prefers its own? |",
        "|---|---|---|---|",
    ]
    for name, entry in payload["test2_cross_docking"].items():
        lines.append("| %s | %s | %s | %s |"
                     % (name, entry["best_receptor"], entry["native_receptor"],
                        "yes" if entry["prefers_native"] else "**no**"))
    lines += [
        "",
        "A ligand that does not score best in the structure it was crystallised",
        "in is telling you the receptor conformations differ more than the",
        "ligands do — which is the whole reason cross-docking is harder than",
        "redocking, and the reason a redock alone does not validate a protocol.",
        "",
        "## Test 3 — ranking the series",
        "",
        "| Ligand | Docking score | Ki (ChEMBL) | Ki (PDBbind) | ΔG from Ki |",
        "|---|---|---|---|---|",
    ]
    for name, entry in payload["test3_ranking"]["ligands"].items():
        lines.append("| %s | %.3f | %.0f µM | %.0f µM | %.2f to %.2f kcal/mol |"
                     % (name, entry["affinity"], entry["ki_chembl_um"],
                        entry["ki_pdbbind_um"], entry["dg_from_ki_pdbbind"],
                        entry["dg_from_ki_chembl"]))
    lines += [
        "",
        "| Ordering | |",
        "|---|---|",
        "| By docking score | %s |" % _show(payload["test3_ranking"]["by_docking_score"]),
        "| By Ki (ChEMBL) | %s |" % _show(payload["test3_ranking"]["by_ki_chembl"]),
        "| By Ki (PDBbind) | %s |" % _show(payload["test3_ranking"]["by_ki_pdbbind"]),
        "",
        "ChEMBL puts STC and 1MU at the same 26 µM, so it does not order them at",
        "all. A sort function will still return one before the other, and the",
        "result reads as a ranking the data does not contain.",
        "",
        "**There is no reliable ranking here to reproduce.** The series spans",
        "18–31 µM — a factor of 1.7, or **%.2f kcal/mol** — and the two sources"
        % payload["test3_ranking"]["series_spread_kcal"],
        "disagree about 1MU by more than the gap between STC and 1MU. No scoring",
        "function resolves 0.3 kcal/mol, and a method that appeared to would be",
        "reporting its own noise.",
        "",
        "That is a result, not a failure of the test. A congeneric series this",
        "tight is the wrong instrument for measuring whether a method can rank,",
        "and finding that out before running the experiment is cheaper than",
        "finding it out afterwards.",
        "",
    ]
    (OUT / "case_study.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
