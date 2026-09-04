#!/usr/bin/env python3
"""Shared receptor preparation: one chain, no solvent, disordered side chains
typed down to what the file actually contains.

Extracted so that Chapters 17 and 26 prepare receptors the same way. Two
chapters preparing "the same" receptor by two code paths is how a
cross-docking matrix ends up comparing runs that are not comparable.
"""
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from docking_common import find_tool  # noqa: E402

CATALYTIC = ("SER", "64", "OG")
SITE_CUTOFF = 5.0

# A REMARK 470 residue whose remaining atoms are exactly one of these can be
# typed down honestly. Anything else stops the run: guessing is how a receptor
# acquires atoms nobody observed.
ALA_ATOMS = {"N", "CA", "C", "O", "CB"}
GLY_ATOMS = {"N", "CA", "C", "O"}


def parse(path):
    atoms, missing_atoms, links = [], [], []
    for line in Path(path).read_text().splitlines():
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
        elif line.startswith("LINK"):
            links.append(line.rstrip())
    return atoms, missing_atoms, links


def catalytic_atoms(atoms):
    return [a for a in atoms
            if (a["res"], a["seq"], a["name"]) == CATALYTIC]


def ligand_copies(atoms, ligand_name):
    """Every copy of a ligand with its distance to the catalytic serine.

    Distance, never file order. Nothing in a PDB marks which copy is the one
    you meant, and the first one is not reliably it.
    """
    catalytic = catalytic_atoms(atoms)
    copies = {}
    for a in atoms:
        if a["res"] == ligand_name:
            copies.setdefault((a["chain"], a["seq"]), []).append(a)
    out = []
    for (chain, seq), copy_atoms in sorted(copies.items()):
        near = min(math.dist(a["xyz"], s["xyz"])
                   for a in copy_atoms for s in catalytic)
        out.append({"chain": chain, "seq": seq, "atoms": copy_atoms,
                    "distance_to_ser64_og": round(near, 2),
                    "in_site": near < SITE_CUTOFF})
    return out


def truncations(atoms, missing, chain):
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


def prepare(pdb_path, chain, work_dir, basename):
    """Write a rigid receptor PDBQT for one chain. Returns (path, decisions)."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    atoms, missing, _ = parse(pdb_path)

    to_ala, to_gly, refused = truncations(atoms, missing, chain)
    if refused:
        for r in refused:
            print("    REFUSED: %s has %s -- neither alanine nor glycine"
                  % (r["residue"], r["atoms_present"]))
        sys.exit("%s chain %s: cannot type a disordered residue down honestly"
                 % (pdb_path, chain))

    kept = [a["line"] for a in atoms if a["rec"] == "ATOM" and a["chain"] == chain]
    receptor_pdb = work_dir / ("%s.pdb" % basename)
    receptor_pdb.write_text("\n".join(kept) + "\nEND\n", encoding="utf-8")

    pdbqt = work_dir / ("%s.pdbqt" % basename)
    cmd = [find_tool("mk_prepare_receptor"), "--read_pdb", str(receptor_pdb),
           "-o", str(work_dir / basename), "-p", "--default_altloc", "A"]
    if to_ala:
        cmd += ["-n", "%s:%s=ALA" % (chain, ",".join(to_ala))]
    if to_gly:
        cmd += ["-n", "%s:%s=GLY" % (chain, ",".join(to_gly))]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not pdbqt.exists():
        print(result.stdout + result.stderr)
        sys.exit("receptor preparation failed for %s chain %s" % (pdb_path, chain))

    return pdbqt, {
        "chain": chain,
        "atoms": len(kept),
        "waters": "all deleted",
        "side_chains_typed_as_ala": ["%s:%s" % (chain, s) for s in to_ala],
        "side_chains_typed_as_gly": ["%s:%s" % (chain, s) for s in to_gly],
        "preparation_tool": "meeko mk_prepare_receptor 0.8.0",
    }


def box_from_ligand(lig_atoms, padding=8.0):
    centre = tuple(sum(a["xyz"][i] for a in lig_atoms) / len(lig_atoms)
                   for i in range(3))
    extent = tuple(max(a["xyz"][i] for a in lig_atoms)
                   - min(a["xyz"][i] for a in lig_atoms) for i in range(3))
    size = tuple(round(e + 2 * padding, 2) for e in extent)
    return centre, size, extent
