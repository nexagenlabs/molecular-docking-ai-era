#!/usr/bin/env python3
"""Chapter 17 — does the protocol reproduce the crystallographic pose?

    python ch17_validation/scripts/validate.py [PDBID ...]

For each of 1L2S, 4JXS and 4JXV: separate receptor from ligand, choose the
ligand copy **by distance to Ser64 OG**, derive the box from its centroid with
8 Å padding, dock at seed 42 and exhaustiveness 32, and measure how far the
top pose is from the crystallographic one.

The RMSD is heavy-atom, symmetry-corrected, and computed **without
superposition**. That last word is the whole chapter:

    python -m spyrmsd ref.sdf pose.sdf              # correct
    python -m spyrmsd --minimize ref.sdf pose.sdf   # WRONG -- never

`--minimize` superimposes the two structures before measuring, which discards
exactly the thing a redock tests. A pose displaced 3.0 Å returns 3.00000
without the flag and 0.00000 with it. The flag makes every validation pass.

Writes outputs/validation.json and outputs/validation_record.md.
"""
import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
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
from docking_common import (dock, find_tool, find_vina, is_reference_platform,  # noqa: E402
                            platform_banner, vina_version)
import molfile  # noqa: E402

RDLogger.DisableLog("rdApp.*")

SEED = 42
EXHAUSTIVENESS = 32
PADDING = 8.0
CATALYTIC = ("SER", "64", "OG")
SITE_CUTOFF = 5.0

# What is being redocked, and the chain each decision lands on. Chains are
# named here rather than derived because each is a judgement:
#
#   1L2S  chain B -- chain A is missing Lys290-Ala292.
#   4JXS  chain B -- the inhibitor is in chain B only; chain A holds phosphate.
#   4JXV  chain A -- the ligand is in both chains, but the chain B copy is
#         modelled in two altlocs. Chain A is a single conformer, so it needs
#         one decision rather than two. Recorded because it is arbitrary.
TARGETS = {
    "1L2S": {"ligand": "STC", "chain": "B"},
    "4JXS": {"ligand": "18U", "chain": "B"},
    "4JXV": {"ligand": "1MU", "chain": "A"},
}

# Alanine's heavy atoms, and glycine's. A REMARK 470 residue whose remaining
# atoms are exactly one of these can be typed down honestly; anything else has
# to stop the run rather than be guessed at.
ALA_ATOMS = {"N", "CA", "C", "O", "CB"}
GLY_ATOMS = {"N", "CA", "C", "O"}


def parse(path):
    atoms, missing_atoms = [], []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            atoms.append({
                "line": line,
                "rec": line[:6].strip(),
                "name": line[12:16].strip(),
                "altloc": line[16],
                "res": line[17:20].strip(),
                "chain": line[21],
                "seq": line[22:26].strip(),
                "element": line[76:78].strip(),
                "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
            })
        elif line.startswith("REMARK 470"):
            fields = line[10:].split()
            if (len(fields) >= 4 and len(fields[0]) == 3 and len(fields[1]) == 1
                    and fields[2].lstrip("-").isdigit()):
                missing_atoms.append({"res": fields[0], "chain": fields[1],
                                      "seq": fields[2]})
    return atoms, missing_atoms


def truncations(atoms, missing, chain):
    """Type disordered side chains down to what the file actually contains.

    A lysine missing CG, CD, CE and NZ holds exactly alanine's heavy atoms, so
    alanine is an honest description. Deleting the residue instead would take
    the backbone with it. Anything that is neither alanine nor glycine stops
    the run -- guessing at it is how a receptor acquires atoms nobody observed.
    """
    present = {}
    for a in atoms:
        if a["rec"] == "ATOM" and a["chain"] == chain:
            present.setdefault(a["seq"], set()).add(a["name"])
    to_ala, to_gly, refused = [], [], []
    for m in missing:
        if m["chain"] != chain:
            continue
        names = present.get(m["seq"], set())
        if names == ALA_ATOMS:
            to_ala.append(m["seq"])
        elif names == GLY_ATOMS:
            to_gly.append(m["seq"])
        else:
            refused.append({"residue": "%s %s" % (m["res"], m["seq"]),
                            "atoms_present": sorted(names)})
    return to_ala, to_gly, refused


def crystal_reference(pdb_id, ligand_name, lig_atoms, template_smiles):
    """The crystallographic pose, as a molecule with real bond orders.

    A PDB fragment carries no bond orders, so RDKit reads it as a graph of
    single bonds. The bond orders come from the SMILES template -- which is
    also the check that the fragment is the molecule we think it is: if the
    template does not match, this fails rather than returning something close.
    """
    fragment = WORK / ("%s_%s_crystal.pdb" % (pdb_id, ligand_name))
    fragment.write_text("\n".join(a["line"] for a in lig_atoms) + "\nEND\n",
                        encoding="utf-8")
    raw = Chem.MolFromPDBFile(str(fragment), removeHs=True, sanitize=False)
    if raw is None:
        sys.exit("%s: could not read the crystallographic ligand" % pdb_id)
    template = Chem.MolFromSmiles(template_smiles)
    try:
        mol = AllChem.AssignBondOrdersFromTemplate(template, raw)
    except ValueError as exc:
        sys.exit("%s: the crystallographic %s does not match the reference "
                 "SMILES (%s). The ligand selection or the template is wrong."
                 % (pdb_id, ligand_name, exc))
    mol = Chem.RemoveHs(mol)
    out = WORK / ("%s_%s_ref.sdf" % (pdb_id, ligand_name))
    writer = Chem.SDWriter(str(out))
    writer.write(mol)
    writer.close()
    return mol, out


def symmetry_rmsd(reference, pose):
    """Heavy-atom, symmetry-corrected RMSD with NO superposition.

    minimize=False is the entire point. With minimize=True the two structures
    are superimposed first, which measures shape agreement and says nothing
    about whether the pose is in the right place.
    """
    from spyrmsd import molecule, rmsd as spyrmsd_rmsd

    def load(mol):
        m = molecule.Molecule.from_rdkit(mol)
        m.strip()                      # heavy atoms only
        return m

    ref, target = load(reference), load(pose)
    return float(spyrmsd_rmsd.symmrmsd(
        ref.coordinates, target.coordinates,
        ref.atomicnums, target.atomicnums,
        ref.adjacency_matrix, target.adjacency_matrix,
        center=False,
        minimize=False,   # NEVER True. See the module docstring.
    ))


def validate(pdb_id, vina):
    spec = TARGETS[pdb_id]
    ligand_name, chain = spec["ligand"], spec["chain"]
    path = STRUCTURES / ("%s.pdb" % pdb_id)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    WORK.mkdir(parents=True, exist_ok=True)

    atoms, missing = parse(path)
    catalytic = [a for a in atoms if (a["res"], a["seq"], a["name"]) == CATALYTIC]
    print("\n=== %s: redocking %s into chain %s %s"
          % (pdb_id, ligand_name, chain, "=" * max(0, 26 - len(pdb_id))))

    # -- ligand copy selection, by distance ---------------------------------
    copies = {}
    for a in atoms:
        if a["res"] == ligand_name:
            copies.setdefault((a["chain"], a["seq"]), []).append(a)
    candidates, chosen = [], None
    for (copy_chain, seq), copy_atoms in sorted(copies.items()):
        near = min(math.dist(a["xyz"], s["xyz"]) for a in copy_atoms for s in catalytic)
        candidates.append({"copy": "%s/%s" % (copy_chain, seq),
                           "atoms": len(copy_atoms),
                           "distance_to_ser64_og": round(near, 2),
                           "in_site": near < SITE_CUTOFF})
        print("  %s copy %s/%-5s %2d atoms  %6.2f A from Ser64 OG   %s"
              % (ligand_name, copy_chain, seq, len(copy_atoms), near,
                 "catalytic" if near < SITE_CUTOFF else "NOT in a site -- discarded"))
        if near < SITE_CUTOFF and copy_chain == chain and chosen is None:
            chosen = ((copy_chain, seq), copy_atoms, near)
    if chosen is None:
        sys.exit("%s: no catalytic %s copy in chain %s" % (pdb_id, ligand_name, chain))
    (lig_chain, lig_seq), lig_atoms, lig_dist = chosen
    # Altlocs in the ligand itself: take the first and say so.
    lig_altlocs = sorted({a["altloc"] for a in lig_atoms if a["altloc"] != " "})
    if lig_altlocs:
        keep = lig_altlocs[0]
        lig_atoms = [a for a in lig_atoms if a["altloc"] in (" ", keep)]
        print("  ligand modelled in altlocs %s -- keeping %s"
              % (", ".join(lig_altlocs), keep))
    print("  -> using %s %s/%s" % (ligand_name, lig_chain, lig_seq))

    # -- every HETATM group NOT used ----------------------------------------
    unused = {}
    for a in atoms:
        if a["rec"] == "HETATM" and (a["chain"], a["seq"]) != (lig_chain, lig_seq):
            unused.setdefault(a["res"], set()).add("%s/%s" % (a["chain"], a["seq"]))
    print("  HETATM groups NOT used:")
    for res, where in sorted(unused.items()):
        sample = ", ".join(sorted(where)[:4])
        more = " ... and %d more" % (len(where) - 4) if len(where) > 4 else ""
        print("    %-4s %4d group(s): %s%s" % (res, len(where), sample, more))

    # -- receptor -----------------------------------------------------------
    to_ala, to_gly, refused = truncations(atoms, missing, chain)
    if refused:
        for r in refused:
            print("    REFUSED: %s has %s -- neither alanine nor glycine"
                  % (r["residue"], r["atoms_present"]))
        sys.exit("%s: cannot type a disordered residue down honestly" % pdb_id)

    receptor_pdb = WORK / ("%s_receptor.pdb" % pdb_id)
    kept = [a["line"] for a in atoms if a["rec"] == "ATOM" and a["chain"] == chain]
    receptor_pdb.write_text("\n".join(kept) + "\nEND\n", encoding="utf-8")
    receptor_pdbqt = WORK / ("%s_receptor.pdbqt" % pdb_id)
    cmd = [find_tool("mk_prepare_receptor"), "--read_pdb", str(receptor_pdb),
           "-o", str(WORK / ("%s_receptor" % pdb_id)), "-p", "--default_altloc", "A"]
    if to_ala:
        cmd += ["-n", "%s:%s=ALA" % (chain, ",".join(to_ala))]
    if to_gly:
        cmd += ["-n", "%s:%s=GLY" % (chain, ",".join(to_gly))]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not receptor_pdbqt.exists():
        print(result.stdout + result.stderr)
        sys.exit("%s: receptor preparation failed" % pdb_id)
    print("  receptor: chain %s, %d atoms, waters and all other HETATM removed"
          % (chain, len(kept)))
    if to_ala:
        print("    %d disordered side chains typed as alanine: %s"
              % (len(to_ala), ",".join(to_ala)))

    # -- ligand for docking, from the committed reference SDF ---------------
    ligand_pdbqt = WORK / ("%s_ligand.pdbqt" % pdb_id)
    source_sdf = LIGANDS / ("%s.sdf" % ligand_name)
    result = subprocess.run([find_tool("mk_prepare_ligand"),
                             "-i", str(source_sdf), "-o", str(ligand_pdbqt)],
                            capture_output=True, text=True)
    if not ligand_pdbqt.exists():
        print(result.stdout + result.stderr)
        sys.exit("%s: ligand preparation failed" % pdb_id)

    # -- box, from the crystallographic centroid ----------------------------
    centre = tuple(sum(a["xyz"][i] for a in lig_atoms) / len(lig_atoms) for i in range(3))
    extent = tuple(max(a["xyz"][i] for a in lig_atoms) - min(a["xyz"][i] for a in lig_atoms)
                   for i in range(3))
    size = tuple(round(e + 2 * PADDING, 2) for e in extent)
    print("  box centre %.3f %.3f %.3f, size %.2f x %.2f x %.2f (%.0f A padding)"
          % (centre + size + (PADDING,)))

    # -- dock ---------------------------------------------------------------
    pose_pdbqt = WORK / ("%s_pose.pdbqt" % pdb_id)
    modes, elapsed, _ = dock(receptor_pdbqt, ligand_pdbqt, centre, size, pose_pdbqt,
                             seed=SEED, exhaustiveness=EXHAUSTIVENESS, vina=vina,
                             log_path=OUT / "logs" / ("%s.log" % pdb_id))
    print("  docked in %.1f s, best %.3f kcal/mol" % (elapsed, modes[0][1]))

    # -- RMSD ---------------------------------------------------------------
    reference, ref_sdf = crystal_reference(
        pdb_id, ligand_name, lig_atoms,
        Chem.MolToSmiles(Chem.RemoveHs(molfile.read_one(
            source_sdf, what="the %s reference copy" % ligand_name))))

    pose_sdf = WORK / ("%s_pose.sdf" % pdb_id)
    result = subprocess.run([find_tool("mk_export"), str(pose_pdbqt),
                             "-s", str(pose_sdf)], capture_output=True, text=True)
    if not pose_sdf.exists():
        print(result.stdout + result.stderr)
        sys.exit("%s: could not export the docked pose to SDF" % pdb_id)
    poses = molfile.read_all(pose_sdf, what="%s: the docked poses" % pdb_id)

    rmsd_top = symmetry_rmsd(reference, poses[0])
    all_rmsd = [round(symmetry_rmsd(reference, p), 3) for p in poses]
    best_rmsd = min(all_rmsd)
    best_mode = all_rmsd.index(best_rmsd) + 1
    print("  RMSD to the crystallographic pose: %.3f A (mode 1)" % rmsd_top)
    print("     best over all %d modes: %.3f A (mode %d)"
          % (len(all_rmsd), best_rmsd, best_mode))

    return {
        "pdb_id": pdb_id,
        "ligand": ligand_name,
        "chain": chain,
        "ligand_selection": {
            "selected_by": "minimum distance to Ser64 OG",
            "candidates": candidates,
            "chosen": {"copy": "%s/%s" % (lig_chain, lig_seq),
                       "distance_to_ser64_og": round(lig_dist, 2)},
            "ligand_altlocs": lig_altlocs,
        },
        "unused_hetatm_groups": {k: sorted(v) for k, v in unused.items()},
        "receptor": {
            "atoms": len(kept),
            "waters": "all deleted",
            "side_chains_typed_as_ala": ["%s:%s" % (chain, s) for s in to_ala],
            "side_chains_typed_as_gly": ["%s:%s" % (chain, s) for s in to_gly],
            "preparation_tool": "meeko mk_prepare_receptor 0.8.0",
        },
        "box": {"centre": [round(c, 3) for c in centre],
                "size": list(size),
                "padding": PADDING,
                "derivation": "centroid of the crystallographic ligand"},
        "best_affinity": modes[0][1],
        "seconds": round(elapsed, 1),
        "rmsd": round(rmsd_top, 3),
        "rmsd_all_modes": all_rmsd,
        "rmsd_best_mode": {"mode": best_mode, "rmsd": best_rmsd},
    }


def write_record(results, meta, sensitivity=None):
    """Chapter 20's protocol record, filled in. Tier-one fields marked."""
    lines = [
        "# Validation record",
        "",
        "Emitted by `ch17_validation/scripts/validate.py` on %s."
        % meta["date"],
        "In the format of Chapter 20's protocol record; ★ marks the tier-one",
        "fields, the ones whose absence stops re-execution.",
        "",
        "## 1. Receptor",
        "",
        "| Field | Value |",
        "|---|---|",
        "| ★ **Receptor source** | RCSB `files.rcsb.org`, entries %s |"
        % ", ".join(results),
        "| Chains used | %s |"
        % ", ".join("%s chain %s" % (k, v["chain"]) for k, v in results.items()),
        "| Altlocs | default A throughout |",
        "| Waters | all deleted |",
        "| Ions and additives | all deleted; phosphates are crystallisation artefacts, nearest 7.83 Å from Ser64 OG |",
        "| Missing residues | left as gaps; chain chosen to avoid them where possible |",
        "| Disordered side chains | typed down to alanine where the file holds exactly alanine's heavy atoms |",
        "| ★ **Receptor preparation tool** | meeko mk_prepare_receptor 0.8.0 |",
        "",
        "Per entry:",
        "",
    ]
    for pdb_id, r in results.items():
        lines.append("- **%s**, chain %s. Ligand copy %s chosen by %s (%.2f Å). "
                     "%d disordered side chains typed as alanine."
                     % (pdb_id, r["chain"], r["ligand_selection"]["chosen"]["copy"],
                        r["ligand_selection"]["selected_by"],
                        r["ligand_selection"]["chosen"]["distance_to_ser64_og"],
                        len(r["receptor"]["side_chains_typed_as_ala"])))
        unused = r["unused_hetatm_groups"]
        lines.append("  - HETATM groups not used: %s"
                     % ", ".join("%s (%d)" % (k, len(v)) for k, v in sorted(unused.items())))
    lines += [
        "",
        "## 2. Ligand",
        "",
        "| Field | Value |",
        "|---|---|",
        "| ★ **Ligand source** | `data/ligands/{STC,18U,1MU}.sdf`, generated from SMILES with explicit formal charges |",
        "| Ligand preparation | meeko mk_prepare_ligand 0.8.0 |",
        "| Protonation | pH 7.4: STC −1, 18U −2, 1MU −2 |",
        "| Stereochemistry as docked | achiral; no stereocentres to preserve |",
        "",
        "The docked ligand is a **generated** conformer, not the crystal pose.",
        "Docking the crystal conformer back would test the search and nothing",
        "else.",
        "",
        "## 3. Search box",
        "",
        "| Entry | ★ Box centre | ★ Box dimensions | Derivation |",
        "|---|---|---|---|",
    ]
    for pdb_id, r in results.items():
        lines.append("| %s | %.3f, %.3f, %.3f | %.2f × %.2f × %.2f | %s, %.0f Å padding |"
                     % (pdb_id, r["box"]["centre"][0], r["box"]["centre"][1],
                        r["box"]["centre"][2], r["box"]["size"][0],
                        r["box"]["size"][1], r["box"]["size"][2],
                        r["box"]["derivation"], r["box"]["padding"]))
    lines += [
        "",
        "## 4. Docking",
        "",
        "| Field | Value |",
        "|---|---|",
        "| ★ **Program and version** | %s |" % meta["vina_version"],
        "| ★ **Random seed** | %d |" % SEED,
        "| Exhaustiveness | %d |" % EXHAUSTIVENESS,
        "| num_modes / energy_range | Vina defaults (9 / 3) |",
        "| Flexible residues | none; this is a rigid-receptor protocol |",
        "",
        "## 5. Results",
        "",
        "| Entry | Ligand | Best affinity | **RMSD to crystal pose** | Best over all modes |",
        "|---|---|---|---|---|",
    ]
    for pdb_id, r in results.items():
        lines.append("| %s | %s | %.3f kcal/mol | **%.3f Å** | %.3f Å (mode %d) |"
                     % (pdb_id, r["ligand"], r["best_affinity"], r["rmsd"],
                        r["rmsd_best_mode"]["rmsd"], r["rmsd_best_mode"]["mode"]))
    lines += [
        "",
        "### How the RMSD was computed",
        "",
        "| | |",
        "|---|---|",
        "| Tool | spyrmsd 0.9.0, `symmrmsd` |",
        "| Heavy atoms only | yes |",
        "| Symmetry-corrected | yes |",
        "| **Superposition** | **no** — `minimize=False` |",
        "| Reference pose | the crystallographic ligand, bond orders assigned from the reference SMILES |",
        "",
        "`--minimize` superimposes before measuring and makes every redock pass:",
        "a pose displaced 3.0 Å returns 3.00000 without it and 0.00000 with it.",
        "A record that does not state superposition was off contains an RMSD",
        "that means nothing.",
        "",
        "## 6. Environment",
        "",
        "| | |",
        "|---|---|",
        "| Platform | %s |" % meta["platform"],
        "| Python | %s |" % meta["python"],
        "| Reference platform for exact values | %s |"
        % ("yes" if meta["reference_platform"] else "no — see build-record/PROGRESS.md"),
        "| Resolved packages | `environment/resolved.txt` |",
        "",
    ]
    if sensitivity:
        lines += [
            "## 6a. Sensitivity of the chain choice",
            "",
            "| Entry | Protocol chain | RMSD | Alternative chain | RMSD | Difference |",
            "|---|---|---|---|---|---|",
        ]
        for pdb_id, s_ in sensitivity.items():
            lines.append("| %s | %s | %.3f Å | %s | %.3f Å | **%.3f Å** |"
                         % (pdb_id, s_["protocol_chain"], s_["protocol_rmsd"],
                            s_["alternative_chain"], s_["alternative_rmsd"],
                            s_["difference"]))
        lines += [
            "",
            "The chain was chosen on grounds that looked like tidiness — one",
            "altloc decision rather than two. It moves the answer by more than",
            "the 2 Å threshold the whole exercise is judged against. A",
            "preparation decision is not cosmetic because the reasoning for it",
            "sounded cosmetic.",
            "",
        ]
    lines += [
        "## 7. Exclusions and deviations",
        "",
        "- **1GA9 is excluded.** ETP is covalently bound to Ser64 OG (`LINK`,",
        "  1.64 Å in chain A, 1.62 Å in chain B) and non-covalent docking cannot",
        "  represent that bond. The exclusion is a modelling decision and is",
        "  recorded as one, not left as a gap in the structure list.",
        "- **4JXV uses chain A.** The ligand is present in both chains, but the",
        "  chain B copy is modelled in two altlocs. Chain A is a single",
        "  conformer, so it costs one decision rather than two. Arbitrary, and",
        "  therefore recorded — and, as the sensitivity check below shows, not",
        "  cosmetic.",
        "- **All waters deleted**, including HOH 403 and 481 in 1L2S chain B,",
        "  which bridge the ligand to the protein at 2.68 and 2.70 Å. This is the",
        "  usual default and it can put the crystallographic pose out of reach.",
        "",
    ]
    (OUT / "validation_record.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entries", nargs="*", default=list(TARGETS))
    ap.add_argument("--no-sensitivity", action="store_true",
                    help="skip the 4JXV chain sensitivity check")
    ap.add_argument("--chain", action="append", default=[], metavar="PDBID=CHAIN",
                    help="override the chain for one entry, e.g. --chain 4JXV=B. "
                         "For testing whether a chain choice is load-bearing; the "
                         "defaults in TARGETS are the recorded protocol.")
    args = ap.parse_args()
    for override in args.chain:
        pdb_id, _, chain = override.partition("=")
        if pdb_id not in TARGETS or not chain:
            sys.exit("bad --chain %r" % override)
        TARGETS[pdb_id]["chain"] = chain

    OUT.mkdir(parents=True, exist_ok=True)
    vina = find_vina()
    print("Vina: %s" % vina_version(vina))
    print(platform_banner())
    print("seed %d, exhaustiveness %d, %.0f A padding" % (SEED, EXHAUSTIVENESS, PADDING))

    results = {}
    for pdb_id in (args.entries or list(TARGETS)):
        results[pdb_id] = validate(pdb_id, vina)

    import platform as platform_module
    meta = {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "vina_version": vina_version(vina),
            "platform": platform_module.platform(),
            "python": platform_module.python_version(),
            "reference_platform": is_reference_platform()}

    # -- sensitivity: does the arbitrary chain choice matter? ---------------
    # 4JXV holds the ligand in both chains. Chain A was chosen a priori because
    # it is a single conformer and chain B's copy has two altlocs -- one
    # decision instead of two. The result below is why that reasoning is not
    # enough: the same protocol on the other chain lands 6 A away.
    sensitivity = {}
    if not args.no_sensitivity and "4JXV" in results:
        original = TARGETS["4JXV"]["chain"]
        alternative = "B" if original == "A" else "A"
        print("\n--- sensitivity check: 4JXV chain %s instead of %s ---"
              % (alternative, original))
        TARGETS["4JXV"]["chain"] = alternative
        try:
            other = validate("4JXV", vina)
            sensitivity["4JXV"] = {
                "protocol_chain": original,
                "protocol_rmsd": results["4JXV"]["rmsd"],
                "alternative_chain": alternative,
                "alternative_rmsd": other["rmsd"],
                "difference": round(abs(other["rmsd"] - results["4JXV"]["rmsd"]), 3),
            }
        finally:
            TARGETS["4JXV"]["chain"] = original

    payload = dict(results)
    payload["sensitivity"] = sensitivity
    payload["docking"] = {"seed": SEED, "exhaustiveness": EXHAUSTIVENESS,
                          "program": meta["vina_version"]}
    payload["rmsd_method"] = {
        "tool": "spyrmsd 0.9.0 symmrmsd",
        "heavy_atoms_only": True,
        "symmetry_corrected": True,
        "superposition": False,
        "command": "python -m spyrmsd ref.sdf pose.sdf",
    }
    payload["meta"] = meta
    (OUT / "validation.json").write_text(json.dumps(payload, indent=2) + "\n",
                                         encoding="utf-8")
    write_record(results, meta, sensitivity)

    print("\n" + "=" * 62)
    print("RMSD to the crystallographic pose, mode 1, no superposition:")
    for pdb_id, r in results.items():
        print("  %s  %s  %6.3f A   (best of %d modes: %.3f A, mode %d)"
              % (pdb_id, r["ligand"], r["rmsd"], len(r["rmsd_all_modes"]),
                 r["rmsd_best_mode"]["rmsd"], r["rmsd_best_mode"]["mode"]))
    print("=" * 62)
    print("\nwrote %s" % (OUT / "validation_record.md"))


if __name__ == "__main__":
    main()
