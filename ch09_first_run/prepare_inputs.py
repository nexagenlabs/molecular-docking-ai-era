#!/usr/bin/env python3
"""Prepare the receptor and ligand for Chapter 9's first docking run.

Writes into ch09_first_run/outputs/:

    receptor.pdbqt      1L2S chain B, rigid
    ligand.pdbqt        STC, from the committed reference SDF
    inputs.json         every decision this script made, machine-readable

Nothing here is chosen silently. Each decision below changes the answer, and a
decision that changes the answer and is not written down is the reason two
people get different numbers from "the same" protocol.
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CH = Path(__file__).resolve().parent
OUT = CH / "outputs"
PDB = REPO / "data" / "structures" / "1L2S.pdb"
LIGAND_SDF = REPO / "data" / "ligands" / "STC.sdf"

# 1L2S holds three copies of STC. Two are catalytic; B/3115 sits at the chain
# interface, 22.7 A from either active site. The copy is selected below by
# distance to Ser64 OG rather than named here, because selecting by file order
# is how the wrong copy gets docked without anyone noticing.
CHAIN = "B"                 # chain A is missing Lys290-Ala292
CATALYTIC_CUTOFF = 5.0      # A from Ser64 OG; the interface copy is at 22.7
PADDING = 8.0               # A around the ligand, for the derived box

# Ten chain B side chains are disordered: REMARK 470 lists them as missing their
# distal atoms, so what the file actually contains is N, CA, CB, C and O -- the
# heavy atoms of alanine. They are typed as alanine rather than deleted.
# Deleting them would remove backbone too, and Lys290's centre of mass is only
# 1.1 A outside the 20 A box face. The nearest of the ten is 12.7 A from the box
# centre, so none of them is a binding-site residue.
TRUNCATED_TO_ALA = ["7", "52", "57", "123", "126", "205", "207", "246", "290", "299"]

# The two waters that bridge the ligand to the protein in chain B, at 2.68 and
# 2.70 A. Named rather than merely counted: they are the ones whose removal
# changes what docking can reach.
BRIDGING_WATERS = {"403", "481"}


def meeko(tool):
    """Locate a meeko command line tool, venv first, then PATH."""
    for candidate in (REPO / ".venv" / "Scripts" / f"{tool}.exe",
                      REPO / ".venv" / "bin" / tool):
        if candidate.exists():
            return str(candidate)
    found = shutil.which(tool) or shutil.which(f"{tool}.py")
    if found is None:
        sys.exit(f"{tool} not found. See environment/README.md.")
    return found


def parse(path):
    atoms = []
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
                "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
            })
    return atoms


def run(cmd, what):
    print("\n$ " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"{what} failed")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not PDB.exists():
        sys.exit(f"{PDB} missing -- run: bash data/structures/fetch.sh")
    if not LIGAND_SDF.exists():
        sys.exit(f"{LIGAND_SDF} missing -- run: python data/ligands/generate.py")
    atoms = parse(PDB)

    ser_og = [a for a in atoms
              if a["res"] == "SER" and a["seq"] == "64" and a["name"] == "OG"]
    print("Ser64 OG found in chains: " + ", ".join(a["chain"] for a in ser_og))

    # -- ligand copy selection -----------------------------------------------
    copies = {}
    for a in atoms:
        if a["res"] == "STC":
            copies.setdefault((a["chain"], a["seq"]), []).append(a)
    print("\nSTC copies in the file: %d" % len(copies))
    chosen = None
    for (chain, seq), copy_atoms in sorted(copies.items()):
        near = min(math.dist(a["xyz"], s["xyz"]) for a in copy_atoms for s in ser_og)
        catalytic = near < CATALYTIC_CUTOFF
        note = "catalytic" if catalytic else "NOT in an active site -- discarded"
        print("  %s/%-5s %2d atoms  %6.2f A from nearest Ser64 OG   %s"
              % (chain, seq, len(copy_atoms), near, note))
        if catalytic and chain == CHAIN:
            chosen = ((chain, seq), copy_atoms, near)
    if chosen is None:
        sys.exit("no catalytic STC copy found in chain " + CHAIN)
    (lig_chain, lig_seq), lig_atoms, lig_dist = chosen
    print("\nusing STC %s/%s as the pose reference (%.2f A from Ser64 OG)"
          % (lig_chain, lig_seq, lig_dist))

    # -- every HETATM group NOT used -----------------------------------------
    # Printed in full and by name. Silent ligand mis-picking is the failure this
    # guards against, and the way it happens is a group nobody mentioned.
    unused = {}
    for a in atoms:
        if a["rec"] == "HETATM" and (a["chain"], a["seq"]) != (lig_chain, lig_seq):
            unused.setdefault(a["res"], set()).add("%s/%s" % (a["chain"], a["seq"]))
    print("\nHETATM groups NOT used:")
    for res, where in sorted(unused.items()):
        sample = sorted(where)[:4]
        more = " ... and %d more" % (len(where) - 4) if len(where) > 4 else ""
        print("  %-4s %4d group(s): %s%s" % (res, len(where), ", ".join(sample), more))

    present = sorted(w for w in unused.get("HOH", set())
                     if w.startswith(CHAIN + "/") and w.split("/")[1] in BRIDGING_WATERS)
    if present:
        print("\n  NOTE: %s bridge the ligand to the protein (2.68 and 2.70 A)."
              % ", ".join(present))
        print("  Every water is deleted here. That is the usual default and it is")
        print("  a decision, not a neutral act: it can put the crystallographic")
        print("  pose out of reach of docking. Chapter 17 revisits it.")

    # -- box, derived from the chosen copy -----------------------------------
    centre = tuple(sum(a["xyz"][i] for a in lig_atoms) / len(lig_atoms) for i in range(3))
    extent = tuple(max(a["xyz"][i] for a in lig_atoms) - min(a["xyz"][i] for a in lig_atoms)
                   for i in range(3))
    derived = tuple(e + 2 * PADDING for e in extent)
    longest = max(math.dist(a["xyz"], b["xyz"]) for a in lig_atoms for b in lig_atoms)
    print("\nbox centre (centroid of STC %s/%s): %.3f %.3f %.3f"
          % (lig_chain, lig_seq, centre[0], centre[1], centre[2]))
    print("ligand extent: %.2f x %.2f x %.2f A" % extent)
    print("derived box at %.0f A padding: %.2f x %.2f x %.2f A" % ((PADDING,) + derived))
    print("largest interatomic distance in the ligand: %.2f A" % longest)
    print("  -- a cube smaller than that cannot hold the ligand in every orientation")

    # -- receptor ------------------------------------------------------------
    receptor_pdb = OUT / "receptor_chainB.pdb"
    kept = [a["line"] for a in atoms if a["rec"] == "ATOM" and a["chain"] == CHAIN]
    receptor_pdb.write_text("\n".join(kept) + "\nEND\n")
    print("\nreceptor: chain %s only, %d atoms, every HETATM removed"
          % (CHAIN, len(kept)))

    # Gln250 is the sole altloc in the entry. Taking A is arbitrary, so it is
    # recorded: someone reproducing this has to make the same arbitrary choice.
    altlocs = sorted({"%s %s%s" % (a["res"], a["chain"], a["seq"])
                      for a in atoms if a["altloc"] != " " and a["chain"] == CHAIN})
    print("altlocs in chain %s: %s -- taking altloc A"
          % (CHAIN, ", ".join(altlocs) or "(none)"))

    run([meeko("mk_prepare_receptor"),
         "--read_pdb", str(receptor_pdb),
         "-o", str(OUT / "receptor"),
         "-p",
         "--default_altloc", "A",
         "-n", "%s:%s=ALA" % (CHAIN, ",".join(TRUNCATED_TO_ALA))],
        "receptor preparation")
    print("  wrote receptor.pdbqt, with %s:%s typed as alanine (REMARK 470 side chains)"
          % (CHAIN, ",".join(TRUNCATED_TO_ALA)))

    # -- ligand --------------------------------------------------------------
    # From the committed SDF, never from a PDBQT. PDBQT drops formal charge and
    # reorders atoms, so reading one back would hand us the neutral acid in an
    # order that breaks any RMSD measured against the reference copy.
    run([meeko("mk_prepare_ligand"),
         "-i", str(LIGAND_SDF),
         "-o", str(OUT / "ligand.pdbqt")],
        "ligand preparation")
    print("  wrote ligand.pdbqt from data/ligands/STC.sdf (formal charge -1)")

    (OUT / "inputs.json").write_text(json.dumps({
        "receptor": {
            "pdb_id": "1L2S",
            "url": "https://files.rcsb.org/download/1L2S.pdb",
            "chain": CHAIN,
            "altloc": "A",
            "waters": "all deleted",
            "waters_deleted_count": len(unused.get("HOH", [])),
            "bridging_waters_deleted": present,
            "other_hetatm_removed": {k: sorted(v) for k, v in unused.items()
                                     if k != "HOH"},
            "side_chains_typed_as_ala": ["%s:%s" % (CHAIN, s) for s in TRUNCATED_TO_ALA],
            "preparation_tool": "meeko mk_prepare_receptor 0.8.0",
        },
        "ligand": {
            "file": "data/ligands/STC.sdf",
            "smiles_docked": "c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)[O-])Cl",
            "formal_charge": -1,
            "preparation_tool": "meeko mk_prepare_ligand 0.8.0",
        },
        "reference_pose": {
            "copy": "%s/%s" % (lig_chain, lig_seq),
            "selected_by": "minimum distance to Ser64 OG",
            "distance_to_ser64_og": round(lig_dist, 2),
        },
        "box": {
            "centre": [round(c, 3) for c in centre],
            "derivation": "centroid of STC %s/%s" % (lig_chain, lig_seq),
            "ligand_extent": [round(e, 2) for e in extent],
            "derived_size_at_8A_padding": [round(d, 2) for d in derived],
            "longest_interatomic_distance": round(longest, 2),
        },
    }, indent=2) + "\n")
    print("\nwrote " + str(OUT / "inputs.json"))


if __name__ == "__main__":
    main()
