#!/usr/bin/env python3
"""Chapter 23 — what the pose is actually touching.

    python ch23_interactions/scripts/fingerprint.py

An RMSD is one number for a whole molecule. It says a pose is 1.1 Å from the
crystallographic one; it does not say whether the pose makes the interactions
the crystal structure makes. Those are different questions and they can
disagree in both directions.

This computes an interaction fingerprint for the crystallographic pose and for
the docked pose of the same ligand, and compares them residue by residue.

Detection is geometric and deliberately simple — distance and, for stacking,
angle. No pharmacophore model, no scoring function, nothing that could be
tuned to produce a nicer answer.

Writes outputs/fingerprint.json and outputs/fingerprint.md.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"

sys.path.insert(0, str(REPO / "scripts"))
import molfile  # noqa: E402
import receptor_prep  # noqa: E402

RDLogger.DisableLog("rdApp.*")

CRYSTAL = "1L2S"
CHAIN = "B"
LIGAND = "STC"

# Cutoffs, all standard and all stated. Each is a threshold on a continuum, so
# a contact just outside one is not absent -- it is just outside, and a
# fingerprint that hides that is a fingerprint that invents precision.
HYDROPHOBIC = 4.5      # C...C
HBOND = 3.5            # donor/acceptor heavy atom separation
SALT_BRIDGE = 4.0      # charged group centres
STACKING = 5.5         # aromatic ring centroids
STACKING_ANGLE = 30.0  # degrees from parallel, for face-to-face

DONORS_ACCEPTORS = {"N", "O", "S"}
POSITIVE = {("ARG", "NH1"), ("ARG", "NH2"), ("ARG", "NE"), ("LYS", "NZ"),
            ("HIS", "ND1"), ("HIS", "NE2")}
NEGATIVE = {("ASP", "OD1"), ("ASP", "OD2"), ("GLU", "OE1"), ("GLU", "OE2")}
AROMATIC_RINGS = {
    "PHE": ["CG", "CD1", "CD2", "CE1", "CE2", "CZ"],
    "TYR": ["CG", "CD1", "CD2", "CE1", "CE2", "CZ"],
    "TRP": ["CD2", "CE2", "CE3", "CZ2", "CZ3", "CH2"],
    "HIS": ["CG", "ND1", "CD2", "CE1", "NE2"],
}


def ligand_features(mol):
    """Heavy atoms, their elements, formal charges, and aromatic rings."""
    conformer = mol.GetConformer()
    atoms = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 1:
            continue
        position = conformer.GetAtomPosition(atom.GetIdx())
        atoms.append({"idx": atom.GetIdx(), "symbol": atom.GetSymbol(),
                      "charge": atom.GetFormalCharge(),
                      "aromatic": atom.GetIsAromatic(),
                      "xyz": (position.x, position.y, position.z)})
    rings = []
    for ring in mol.GetRingInfo().AtomRings():
        if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            coords = np.array([[conformer.GetAtomPosition(i).x,
                                conformer.GetAtomPosition(i).y,
                                conformer.GetAtomPosition(i).z] for i in ring])
            centroid = coords.mean(axis=0)
            # Ring normal from the first three atoms; adequate for a planar
            # aromatic ring and it needs no least-squares fit.
            normal = np.cross(coords[1] - coords[0], coords[2] - coords[0])
            normal = normal / np.linalg.norm(normal)
            rings.append({"centroid": centroid, "normal": normal,
                          "size": len(ring)})
    return atoms, rings


def protein_rings(residue_atoms, res_name):
    names = AROMATIC_RINGS.get(res_name)
    if not names:
        return None
    coords = [residue_atoms[n] for n in names if n in residue_atoms]
    if len(coords) < 3:
        return None
    coords = np.array(coords)
    centroid = coords.mean(axis=0)
    normal = np.cross(coords[1] - coords[0], coords[2] - coords[0])
    return {"centroid": centroid, "normal": normal / np.linalg.norm(normal)}


def fingerprint(protein, lig_atoms, lig_rings):
    """Residue -> set of interaction types, with the closest distance for each."""
    residues = {}
    for a in protein:
        key = (a["res"], a["chain"], a["seq"])
        residues.setdefault(key, {})[a["name"]] = np.array(a["xyz"])

    found = {}

    def record(key, kind, distance, detail):
        label = "%s%s" % (key[0].title(), key[2])
        entry = found.setdefault(label, {})
        if kind not in entry or distance < entry[kind]["distance"]:
            entry[kind] = {"distance": round(float(distance), 2), "detail": detail}

    for key, atom_map in residues.items():
        res_name = key[0]
        for name, position in atom_map.items():
            for lig in lig_atoms:
                distance = float(np.linalg.norm(position - np.array(lig["xyz"])))
                if distance > 6.0:
                    continue
                # hydrophobic: carbon to carbon
                if (distance <= HYDROPHOBIC and name.startswith("C")
                        and lig["symbol"] == "C"):
                    record(key, "hydrophobic", distance, "%s...C" % name)
                # hydrogen bond: two heteroatoms close enough
                if (distance <= HBOND and name[:1] in DONORS_ACCEPTORS
                        and lig["symbol"] in DONORS_ACCEPTORS):
                    record(key, "hbond", distance, "%s...%s" % (name, lig["symbol"]))
                # salt bridge: formally charged groups of opposite sign
                if distance <= SALT_BRIDGE:
                    if (res_name, name) in POSITIVE and lig["charge"] < 0:
                        record(key, "salt_bridge", distance, "%s...%s-" % (name, lig["symbol"]))
                    elif (res_name, name) in NEGATIVE and lig["charge"] > 0:
                        record(key, "salt_bridge", distance, "%s...%s+" % (name, lig["symbol"]))

        ring = protein_rings(atom_map, res_name)
        if ring is not None:
            for lig_ring in lig_rings:
                distance = float(np.linalg.norm(ring["centroid"] - lig_ring["centroid"]))
                if distance <= STACKING:
                    cosine = abs(float(np.dot(ring["normal"], lig_ring["normal"])))
                    angle = math.degrees(math.acos(min(1.0, cosine)))
                    kind = "pi_stack" if angle <= STACKING_ANGLE else "pi_edge"
                    record(key, kind, distance, "%.0f deg" % angle)

    return found


def load_pose(path):
    return molfile.read_all(path, what="the pose in %s" % path.name)[0]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    crystal_sdf = REPO / "ch17_validation" / "outputs" / "work" / "1L2S_STC_ref.sdf"
    docked_sdf = REPO / "ch17_validation" / "outputs" / "work" / "1L2S_pose.sdf"
    for path in (crystal_sdf, docked_sdf):
        if not path.exists():
            sys.exit("%s missing -- run ch17_validation/run.sh first" % path)

    atoms, _, _ = receptor_prep.parse(STRUCTURES / ("%s.pdb" % CRYSTAL))
    protein = [a for a in atoms if a["rec"] == "ATOM" and a["chain"] == CHAIN]

    prints = {}
    for label, path in (("crystal", crystal_sdf), ("docked", docked_sdf)):
        mol = load_pose(path)
        lig_atoms, lig_rings = ligand_features(mol)
        prints[label] = fingerprint(protein, lig_atoms, lig_rings)
        print("%s pose: %d heavy atoms, %d aromatic rings, %d residues contacted"
              % (label, len(lig_atoms), len(lig_rings), len(prints[label])))

    crystal_set = {(r, k) for r, kinds in prints["crystal"].items() for k in kinds}
    docked_set = {(r, k) for r, kinds in prints["docked"].items() for k in kinds}
    shared = crystal_set & docked_set
    missed = crystal_set - docked_set
    invented = docked_set - crystal_set

    print("\nInteractions in the crystallographic pose: %d" % len(crystal_set))
    print("           reproduced by the docked pose: %d (%.0f%%)"
          % (len(shared), 100 * len(shared) / max(len(crystal_set), 1)))
    print("                                  missed: %d" % len(missed))
    print("        present in the docked pose only: %d" % len(invented))

    if missed:
        print("\nMissed:")
        for residue, kind in sorted(missed):
            print("   %-9s %s (%.2f A in the crystal)"
                  % (residue, kind, prints["crystal"][residue][kind]["distance"]))
    if invented:
        print("\nOnly in the docked pose:")
        for residue, kind in sorted(invented):
            print("   %-9s %s (%.2f A)"
                  % (residue, kind, prints["docked"][residue][kind]["distance"]))

    recovery = len(shared) / max(len(crystal_set), 1)
    print("\nThe pose is 1.114 A from the crystallographic one and reproduces")
    print("%.0f%% of its interactions. Those are two different measurements and"
          % (100 * recovery))
    print("neither implies the other: a pose can sit close and miss the contact")
    print("that matters, or sit further away and make every one of them.")

    payload = {
        "crystal": CRYSTAL, "chain": CHAIN, "ligand": LIGAND,
        "cutoffs": {"hydrophobic": HYDROPHOBIC, "hbond": HBOND,
                    "salt_bridge": SALT_BRIDGE, "stacking": STACKING,
                    "stacking_angle": STACKING_ANGLE},
        "fingerprints": prints,
        "shared": sorted("%s:%s" % pair for pair in shared),
        "missed": sorted("%s:%s" % pair for pair in missed),
        "docked_only": sorted("%s:%s" % pair for pair in invented),
        "recovery": round(recovery, 3),
        "rmsd_for_context": 1.114,
    }
    (OUT / "fingerprint.json").write_text(json.dumps(payload, indent=2) + "\n",
                                          encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "fingerprint.json"))


def write_report(payload):
    prints = payload["fingerprints"]
    residues = sorted(set(prints["crystal"]) | set(prints["docked"]),
                      key=lambda r: int("".join(c for c in r if c.isdigit()) or 0))
    lines = [
        "# Chapter 23 — interaction fingerprints", "",
        "The crystallographic pose of %s in %s chain %s, against the pose docked"
        % (payload["ligand"], payload["crystal"], payload["chain"]),
        "in Chapter 17 — which is **%.3f Å** away by symmetry-corrected RMSD."
        % payload["rmsd_for_context"],
        "",
        "| Residue | Crystal pose | Docked pose | |",
        "|---|---|---|---|",
    ]
    for residue in residues:
        crystal = prints["crystal"].get(residue, {})
        docked = prints["docked"].get(residue, {})
        both = sorted(set(crystal) | set(docked))
        crystal_text = ", ".join("%s %.2f Å" % (k, crystal[k]["distance"])
                                 for k in both if k in crystal) or "—"
        docked_text = ", ".join("%s %.2f Å" % (k, docked[k]["distance"])
                                for k in both if k in docked) or "—"
        if set(crystal) == set(docked):
            verdict = "same"
        elif set(crystal) - set(docked):
            verdict = "**missed**"
        else:
            verdict = "extra"
        lines.append("| %s | %s | %s | %s |"
                     % (residue, crystal_text, docked_text, verdict))
    lines += [
        "",
        "**%.0f%% of the crystallographic interactions are reproduced.**"
        % (100 * payload["recovery"]),
        "",
        "| | Count |",
        "|---|---|",
        "| In both | %d |" % len(payload["shared"]),
        "| In the crystal pose only (missed) | %d |" % len(payload["missed"]),
        "| In the docked pose only | %d |" % len(payload["docked_only"]),
        "",
        "An RMSD is one number for a whole molecule. It says the pose is %.3f Å"
        % payload["rmsd_for_context"],
        "away; it does not say which contacts survived that distance. The two",
        "measurements can disagree in both directions — a pose can sit close and",
        "miss the interaction the chemistry depends on, or sit further away and",
        "make every one of them.",
        "",
        "## Cutoffs",
        "",
        "| Interaction | Cutoff |",
        "|---|---|",
        "| Hydrophobic (C···C) | %.1f Å |" % payload["cutoffs"]["hydrophobic"],
        "| Hydrogen bond (heteroatom···heteroatom) | %.1f Å |" % payload["cutoffs"]["hbond"],
        "| Salt bridge | %.1f Å |" % payload["cutoffs"]["salt_bridge"],
        "| Aromatic stacking (centroid···centroid) | %.1f Å |" % payload["cutoffs"]["stacking"],
        "| Face-to-face, if within | %.0f° of parallel |" % payload["cutoffs"]["stacking_angle"],
        "",
        "Every one is a threshold on a continuum. A contact at 3.6 Å is not",
        "absent from a 3.5 Å hydrogen-bond criterion — it is just outside it, and",
        "a fingerprint that renders that as a clean 0 has invented precision the",
        "geometry does not have. Detection here is distance and angle only: no",
        "pharmacophore model and no scoring function, so there is nothing to tune",
        "toward a nicer answer.",
        "",
    ]
    (OUT / "fingerprint.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
