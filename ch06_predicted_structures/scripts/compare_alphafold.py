#!/usr/bin/env python3
"""Chapter 6 — can you dock into a predicted structure?

    python ch06_predicted_structures/scripts/compare_alphafold.py

Fetches the AlphaFold model of AmpC (UniProt P00811), lines it up against the
1L2S crystal structure, and then does the only test that settles the question:
**docks STC into the predicted structure and measures the pose against the
crystallographic one.**

Two things are checked before that, because getting either wrong makes the
docking meaningless:

1. **The numbering.** UniProt numbering is not PDB numbering. The offset is
   verified from the sequences rather than assumed, because a script that
   applies a remembered offset to the wrong model selects the wrong residues
   and says nothing.
2. **The confidence.** A pLDDT for the binding site, not for the whole chain.
   A model can average 90 and still be useless where it matters.

Writes outputs/alphafold_comparison.json and .md.
"""
import json
import math
import subprocess
import sys
import urllib.request
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

UNIPROT = "P00811"
AF_URL = "https://alphafold.ebi.ac.uk/files/AF-%s-F1-model_v6.pdb" % UNIPROT
CRYSTAL = "1L2S"
CRYSTAL_CHAIN = "B"
LIGAND = "STC"
SEED = 42
EXHAUSTIVENESS = 32
PADDING = 8.0

# Binding-site residues in PDB numbering. The UniProt numbers are computed, not
# typed: that is the point of this chapter.
SITE_PDB = ["64", "67", "119", "120", "150", "152", "221", "293",
            "315", "316", "317", "318", "346", "349"]

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}


def fetch_model():
    path = STRUCTURES / ("AF-%s-F1.pdb" % UNIPROT)
    if path.exists():
        print("AlphaFold model already present: %s" % path.name)
        return path
    print("fetching %s" % AF_URL)
    with urllib.request.urlopen(AF_URL, timeout=120) as response:
        path.write_bytes(response.read())
    return path


def residues(atoms, chain=None):
    """seq -> {"res": name, "atoms": {name: xyz}} for one chain."""
    out = {}
    for a in atoms:
        if a["rec"] != "ATOM":
            continue
        if chain is not None and a["chain"] != chain:
            continue
        if a["altloc"] not in (" ", "A"):
            continue
        entry = out.setdefault(a["seq"], {"res": a["res"], "atoms": {}})
        entry["atoms"][a["name"]] = a["xyz"]
    return out


def sequence(res_map):
    keys = sorted(res_map, key=int)
    return "".join(THREE_TO_ONE.get(res_map[k]["res"], "X") for k in keys), keys


def find_offset(crystal_res, model_res):
    """Recover the UniProt-minus-PDB offset by matching sequences.

    Verified, not assumed. CLAUDE.md says the offset is 16; this function has
    to agree with that from the coordinates, and if it ever does not, the model
    or the entry has changed and everything downstream is void.
    """
    crystal_seq, crystal_keys = sequence(crystal_res)
    model_seq, model_keys = sequence(model_res)
    position = model_seq.find(crystal_seq[:40])
    if position < 0:
        # Fall back to a per-offset residue-identity vote, which tolerates the
        # odd mutation or unmodelled residue at the N-terminus.
        best, best_score = None, -1
        for offset in range(-50, 101):
            score = sum(1 for k in crystal_keys
                        if str(int(k) + offset) in model_res
                        and model_res[str(int(k) + offset)]["res"] == crystal_res[k]["res"])
            if score > best_score:
                best, best_score = offset, score
        return best, best_score / len(crystal_keys)
    offset = int(model_keys[position]) - int(crystal_keys[0])
    matches = sum(1 for k in crystal_keys
                  if str(int(k) + offset) in model_res
                  and model_res[str(int(k) + offset)]["res"] == crystal_res[k]["res"])
    return offset, matches / len(crystal_keys)


def kabsch(mobile, target):
    """Rotation and translation putting `mobile` onto `target`."""
    mobile_centre = mobile.mean(axis=0)
    target_centre = target.mean(axis=0)
    correlation = (mobile - mobile_centre).T @ (target - target_centre)
    u, _, vt = np.linalg.svd(correlation)
    sign = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ np.diag([1.0, 1.0, sign]) @ u.T
    return rotation, target_centre - rotation @ mobile_centre


def apply_transform(path, out_path, rotation, translation):
    """Rewrite a PDB with every coordinate transformed."""
    lines = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            moved = rotation @ xyz + translation
            line = "%s%8.3f%8.3f%8.3f%s" % (line[:30], moved[0], moved[1],
                                            moved[2], line[54:])
        lines.append(line)
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    crystal_path = STRUCTURES / ("%s.pdb" % CRYSTAL)
    if not crystal_path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % crystal_path)
    model_path = fetch_model()

    crystal_atoms, _, _ = receptor_prep.parse(crystal_path)
    model_atoms, _, _ = receptor_prep.parse(model_path)
    crystal_res = residues(crystal_atoms, CRYSTAL_CHAIN)
    model_res = residues(model_atoms)

    # -- 1. the numbering ---------------------------------------------------
    offset, identity = find_offset(crystal_res, model_res)
    print("\n1. NUMBERING")
    print("   crystal chain %s: %d residues; model: %d residues"
          % (CRYSTAL_CHAIN, len(crystal_res), len(model_res)))
    print("   offset recovered from the sequences: UniProt = PDB + %d" % offset)
    print("   residue identity at that offset: %.1f%%" % (100 * identity))
    if identity < 0.9:
        sys.exit("sequences do not match at any offset -- stop here")

    site = []
    for pdb_seq in SITE_PDB:
        uniprot_seq = str(int(pdb_seq) + offset)
        crystal_name = crystal_res[pdb_seq]["res"]
        model_name = model_res.get(uniprot_seq, {}).get("res")
        wrong_name = model_res.get(pdb_seq, {}).get("res")
        site.append({"pdb": pdb_seq, "uniprot": uniprot_seq,
                     "crystal_residue": crystal_name,
                     "model_residue": model_name,
                     "model_residue_at_pdb_number": wrong_name,
                     "matches": crystal_name == model_name})
    print("\n   %-6s %-9s %-9s %-9s %s"
          % ("PDB", "UniProt", "crystal", "model", "model at the PDB number"))
    for entry in site[:5]:
        print("   %-6s %-9s %-9s %-9s %s"
              % (entry["pdb"], entry["uniprot"], entry["crystal_residue"],
                 entry["model_residue"], entry["model_residue_at_pdb_number"]))
    print("   ... %d site residues, %d matching at the corrected numbering"
          % (len(site), sum(1 for e in site if e["matches"])))
    print("\n   Ser%s in the crystal is Ser%s in the model. Look up the PDB"
          % (SITE_PDB[0], str(int(SITE_PDB[0]) + offset)))
    print("   number in the model and you get %s -- a different residue, no error."
          % site[0]["model_residue_at_pdb_number"])

    # -- 2. confidence ------------------------------------------------------
    # AlphaFold writes pLDDT into the B-factor column. Whole-chain averages
    # hide exactly what matters: a model can average 90 and be useless in the
    # pocket, and the pocket is the only part docking uses.
    plddt = {}
    for line in model_path.read_text().splitlines():
        if line.startswith("ATOM"):
            plddt.setdefault(line[22:26].strip(), []).append(float(line[60:66]))
    overall = np.mean([v for values in plddt.values() for v in values])
    site_plddt = {e["pdb"]: float(np.mean(plddt[e["uniprot"]]))
                  for e in site if e["uniprot"] in plddt}
    print("\n2. CONFIDENCE (pLDDT)")
    print("   whole chain: %.1f" % overall)
    print("   binding site: %.1f (lowest %s at %.1f)"
          % (np.mean(list(site_plddt.values())),
             min(site_plddt, key=site_plddt.get), min(site_plddt.values())))

    # -- 3. superpose and measure -------------------------------------------
    common = [(k, str(int(k) + offset)) for k in crystal_res
              if str(int(k) + offset) in model_res
              and "CA" in crystal_res[k]["atoms"]
              and "CA" in model_res[str(int(k) + offset)]["atoms"]]
    mobile = np.array([model_res[m]["atoms"]["CA"] for _, m in common])
    target = np.array([crystal_res[c]["atoms"]["CA"] for c, _ in common])
    rotation, translation = kabsch(mobile, target)
    moved = (rotation @ mobile.T).T + translation
    backbone_rmsd = float(np.sqrt(((moved - target) ** 2).sum(axis=1).mean()))

    site_pairs = [(c, m) for c, m in common if c in SITE_PDB]
    site_mobile = np.array([model_res[m]["atoms"]["CA"] for _, m in site_pairs])
    site_target = np.array([crystal_res[c]["atoms"]["CA"] for c, _ in site_pairs])
    site_moved = (rotation @ site_mobile.T).T + translation
    site_rmsd = float(np.sqrt(((site_moved - site_target) ** 2).sum(axis=1).mean()))

    # Side chains, per site residue. The backbone can agree beautifully while
    # the atoms that actually line the pocket sit somewhere else -- and a
    # docking box is mostly full of side chains.
    side_chain = {}
    backbone_names = {"N", "CA", "C", "O"}
    for c, m in site_pairs:
        shared = [n for n in crystal_res[c]["atoms"]
                  if n in model_res[m]["atoms"] and n not in backbone_names
                  and not n.startswith("H")]
        if not shared:
            continue
        crystal_xyz = np.array([crystal_res[c]["atoms"][n] for n in shared])
        model_xyz = np.array([model_res[m]["atoms"][n] for n in shared])
        model_moved = (rotation @ model_xyz.T).T + translation
        side_chain[c] = float(np.sqrt(((model_moved - crystal_xyz) ** 2)
                                      .sum(axis=1).mean()))

    print("\n3. GEOMETRY, after superposition on %d matched CA atoms" % len(common))
    print("   whole-chain backbone RMSD: %.3f A" % backbone_rmsd)
    print("   binding-site CA RMSD:      %.3f A" % site_rmsd)
    if side_chain:
        worst = max(side_chain, key=side_chain.get)
        print("   binding-site SIDE CHAINS:  %.3f A mean, worst %s at %.3f A"
              % (np.mean(list(side_chain.values())), worst, side_chain[worst]))
        for residue in sorted(side_chain, key=side_chain.get, reverse=True)[:4]:
            print("     %-5s %s  %.2f A"
                  % (residue, crystal_res[residue]["res"], side_chain[residue]))

    # -- 4. the test that settles it ----------------------------------------
    aligned = WORK / "af_model_aligned.pdb"
    apply_transform(model_path, aligned, rotation, translation)
    receptor_pdbqt, decisions = receptor_prep.prepare(aligned, "A", WORK, "af_receptor")

    ligand_pdbqt = WORK / ("%s.pdbqt" % LIGAND)
    subprocess.run([find_tool("mk_prepare_ligand"),
                    "-i", str(LIGANDS / ("%s.sdf" % LIGAND)), "-o", str(ligand_pdbqt)],
                   capture_output=True, text=True)
    if not ligand_pdbqt.exists():
        sys.exit("ligand preparation failed")

    copies = [c for c in receptor_prep.ligand_copies(crystal_atoms, LIGAND)
              if c["in_site"] and c["chain"] == CRYSTAL_CHAIN]
    lig_atoms = copies[0]["atoms"]
    centre, size, _ = receptor_prep.box_from_ligand(lig_atoms, PADDING)

    vina = find_vina()
    pose = WORK / "af_pose.pdbqt"
    modes, elapsed, _ = dock(receptor_pdbqt, ligand_pdbqt, centre, size, pose,
                             seed=SEED, exhaustiveness=EXHAUSTIVENESS, vina=vina,
                             log_path=OUT / "logs" / "af_dock.log")

    fragment = WORK / "crystal_ligand.pdb"
    fragment.write_text("\n".join(a["line"] for a in lig_atoms) + "\nEND\n",
                        encoding="utf-8")
    raw = Chem.MolFromPDBFile(str(fragment), removeHs=True, sanitize=False)
    template = Chem.MolToSmiles(Chem.RemoveHs(next(Chem.SDMolSupplier(
        str(LIGANDS / ("%s.sdf" % LIGAND)), removeHs=False))))
    reference = Chem.RemoveHs(AllChem.AssignBondOrdersFromTemplate(
        Chem.MolFromSmiles(template), raw))

    pose_sdf = WORK / "af_pose.sdf"
    subprocess.run([find_tool("mk_export"), str(pose), "-s", str(pose_sdf)],
                   capture_output=True, text=True)
    poses = [m for m in Chem.SDMolSupplier(str(pose_sdf), removeHs=True) if m]

    from spyrmsd import molecule, rmsd as spyrmsd_rmsd

    def load(mol):
        m = molecule.Molecule.from_rdkit(mol)
        m.strip()
        return m

    ref_mol = load(reference)

    def rmsd_of(p):
        target_mol = load(p)
        return float(spyrmsd_rmsd.symmrmsd(
            ref_mol.coordinates, target_mol.coordinates,
            ref_mol.atomicnums, target_mol.atomicnums,
            ref_mol.adjacency_matrix, target_mol.adjacency_matrix,
            center=False, minimize=False))

    af_rmsd = rmsd_of(poses[0])
    af_best = min(rmsd_of(p) for p in poses)
    print("\n4. DOCKING INTO THE PREDICTED STRUCTURE")
    print("   best affinity %.3f kcal/mol in %.1f s" % (modes[0][1], elapsed))
    print("   RMSD to the crystallographic pose: %.3f A (mode 1)" % af_rmsd)
    print("   best over %d modes: %.3f A" % (len(poses), af_best))
    print("\n   Compare Chapter 17, which docks into the crystal structure")
    print("   itself with the same protocol and gets 1.114 A.")

    payload = {
        "uniprot": UNIPROT, "model_url": AF_URL, "crystal": CRYSTAL,
        "crystal_chain": CRYSTAL_CHAIN,
        "numbering": {"offset_uniprot_minus_pdb": offset,
                      "residue_identity": round(identity, 4),
                      "site": site},
        "confidence": {"whole_chain_plddt": round(float(overall), 1),
                       "site_plddt": {k: round(v, 1) for k, v in site_plddt.items()},
                       "site_mean_plddt": round(float(np.mean(list(site_plddt.values()))), 1)},
        "geometry": {"matched_ca_atoms": len(common),
                     "backbone_rmsd": round(backbone_rmsd, 3),
                     "site_ca_rmsd": round(site_rmsd, 3),
                     "site_side_chain_rmsd": {k: round(v, 3)
                                              for k, v in side_chain.items()},
                     "site_side_chain_mean": round(float(np.mean(
                         list(side_chain.values()))), 3) if side_chain else None},
        "docking": {"seed": SEED, "exhaustiveness": EXHAUSTIVENESS,
                    "program": vina_version(vina),
                    "receptor": decisions,
                    "box_centre": [round(c, 3) for c in centre],
                    "box_size": list(size),
                    "best_affinity": modes[0][1],
                    "rmsd_to_crystal_pose": round(af_rmsd, 3),
                    "rmsd_best_mode": round(af_best, 3),
                    "crystal_structure_reference_rmsd": 1.114},
    }
    (OUT / "alphafold_comparison.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "alphafold_comparison.json"))


def write_report(payload):
    numbering = payload["numbering"]
    lines = [
        "# Chapter 6 — docking into a predicted structure", "",
        "AlphaFold model of AmpC (UniProt %s) against %s chain %s."
        % (payload["uniprot"], payload["crystal"], payload["crystal_chain"]),
        "",
        "## 1. The numbering trap",
        "",
        "**UniProt number = PDB number + %d**, recovered from the sequences here"
        % numbering["offset_uniprot_minus_pdb"],
        "rather than assumed, at %.1f%% residue identity."
        % (100 * numbering["residue_identity"]),
        "",
        "| PDB | UniProt | Crystal | Model | Model at the PDB number |",
        "|---|---|---|---|---|",
    ]
    for entry in numbering["site"]:
        lines.append("| %s | %s | %s | %s | %s |"
                     % (entry["pdb"], entry["uniprot"], entry["crystal_residue"],
                        entry["model_residue"],
                        entry["model_residue_at_pdb_number"] or "—"))
    first = numbering["site"][0]
    lines += [
        "",
        "Read the last column. Look up residue %s in the model — the number the"
        % first["pdb"],
        "crystal structure uses — and you get **%s**, not the catalytic serine."
        % (first["model_residue_at_pdb_number"] or "nothing"),
        "No error is raised. Everything downstream is about a different residue.",
        "",
        "## 2. Confidence where it matters",
        "",
        "| | pLDDT |",
        "|---|---|",
        "| Whole chain | %.1f |" % payload["confidence"]["whole_chain_plddt"],
        "| Binding site | %.1f |" % payload["confidence"]["site_mean_plddt"],
        "",
        "AlphaFold writes pLDDT into the B-factor column. A whole-chain average",
        "hides the only part docking uses: a model can average 90 and be useless",
        "in the pocket.",
        "",
        "## 3. Geometry",
        "",
        "| | RMSD |",
        "|---|---|",
        "| Whole-chain backbone (%d CA atoms) | %.3f Å |"
        % (payload["geometry"]["matched_ca_atoms"], payload["geometry"]["backbone_rmsd"]),
        "| Binding-site CA | %.3f Å |" % payload["geometry"]["site_ca_rmsd"],
        "| Binding-site side chains | %.3f Å |"
        % (payload["geometry"]["site_side_chain_mean"] or 0.0),
        "",
        "Worst side chains:",
        "",
        "| Residue | RMSD |",
        "|---|---|",
    ] + [
        "| %s | %.2f Å |" % (k, v) for k, v in
        sorted(payload["geometry"]["site_side_chain_rmsd"].items(),
               key=lambda kv: -kv[1])[:5]
    ] + [
        "",
        "## 4. The test that settles it",
        "",
        "Backbone agreement is not the question. The question is whether a pose",
        "docked into the prediction lands where the crystallographic one is.",
        "",
        "| | RMSD to the crystal pose |",
        "|---|---|",
        "| Docked into the AlphaFold model | **%.3f Å** |"
        % payload["docking"]["rmsd_to_crystal_pose"],
        "| Docked into the crystal structure (Chapter 17) | %.3f Å |"
        % payload["docking"]["crystal_structure_reference_rmsd"],
        "",
        "Same ligand, same box, same seed, same exhaustiveness. The only",
        "difference is the receptor.",
        "",
    ]
    (OUT / "alphafold_comparison.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
